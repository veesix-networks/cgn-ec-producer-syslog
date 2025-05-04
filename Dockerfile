FROM balabit/syslog-ng:4.8.0

RUN apt-get update && apt-get install -y python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

WORKDIR /app

ADD syslog.yaml /etc/cgn_ec/syslog.yaml

EXPOSE 1514/udp

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY . /app
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
