from pydantic import Field, ValidationError, BaseModel
from pydantic_settings import BaseSettings
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import yaml


class VendorRegexMap(BaseModel):
    session_mapping: str | list[str] = None
    address_mapping: str | list[str] = None
    port_mapping: str | list[str] = None
    port_block_mapping: str | list[str] = None
    default_pattern: str | None = None


class VendorConfig(BaseModel):
    name: str
    regex_map: VendorRegexMap


class Settings(BaseSettings):
    HOST: str = Field(default="0.0.0.0", description="Listen on a specific interface")
    PORT: int = Field(default=1514, description="Syslog port to listen on")
    CONFIG: str = Field(
        default="/etc/cgn_ec/syslog.yaml", description="Syslog configuration file"
    )
    KAFKA_QUEUE_BUFFER_MS: int = 500
    KAFKA_BOOTSTRAP_SERVER: str = "10.4.21.133:9094"

    class Config:
        env_file = ".env"


try:
    settings = Settings()
    print("✅ Configuration validation passed!")
except ValidationError as e:
    print("❌ Configuration validation failed:\n")
    for err in e.errors():
        loc = " → ".join(str(x) for x in err["loc"])
        print(f" - {loc}: {err['msg']}")
    exit(1)

TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_NAME = "base_config.j2"
OUTPUT_PATH = Path("/etc/cgn_ec/rendered.conf")


def load_config_file():
    with open(settings.CONFIG) as yaml_file:
        try:
            data = yaml.safe_load(yaml_file)
        except Exception as err:
            print(f"Unable to load '{settings.CONFIG}' due to error: {err}")
            exit()

    return data


def build_rendered_config_file():
    vendor_config = load_config_file()
    if not vendor_config:
        raise ValueError("syslog.yaml is either empty or not correctly formatted.")

    vendors = vendor_config.get("vendors")

    if not vendors or not isinstance(vendors, list) or len(vendors) == 0:
        raise ValueError("Unable to find any vendors in the syslog.yaml.")

    enabled_vendors = [
        VendorConfig.model_validate(vendor)
        for vendor in vendors
        if vendor.get("enabled")
    ]
    valid_vendors = []
    for vendor in enabled_vendors:
        if (
            not vendor.regex_map.address_mapping
            and not vendor.regex_map.session_mapping
            and not vendor.regex_map.port_block_mapping
            and not vendor.regex_map.port_mapping
            and not vendor.regex_map.default_pattern
        ):
            print(
                f"Can not generate config for vendor {vendor.name} due to no regex patterns found."
            )
            continue

        valid_vendors.append(vendor)

    print("Attempting to enable the following vendors:")
    for vendor in valid_vendors:
        print(
            f"- {vendor.name} (includes default_pattern match)"
            if vendor.regex_map.default_pattern
            else f"- {vendor.name}"
        )
    print()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True
    )
    template = env.get_template(TEMPLATE_NAME)
    rendered = template.render(config=settings, vendors=valid_vendors)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered)


if __name__ == "__main__":
    build_rendered_config_file()
