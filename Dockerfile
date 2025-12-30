FROM ubuntu:24.04

LABEL maintainer="zzzz0317"
LABEL description="MailHarbor - Fetchmail + Dovecot Mail Relay Server"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN apt-get update && apt-get install -y \
    fetchmail \
    dovecot-core \
    dovecot-imapd \
    dovecot-lmtpd \
    dovecot-fts-xapian \
    python3 \
    python3-pip \
    python3-yaml \
    python3-jinja2 \
    python3-watchdog \
    python3-bcrypt \
    supervisor \
    netcat-openbsd \
    vim \
    nano \
    locales \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

RUN groupadd -g 5000 vmail && \
    useradd -u 5000 -g vmail -s /usr/sbin/nologin -d /data/mail -M vmail

WORKDIR /app

COPY requirements.txt /app/

RUN pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt

COPY src/ /app/src/
COPY templates/ /app/templates/
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/healthcheck.sh /healthcheck.sh
RUN chmod +x /entrypoint.sh /healthcheck.sh

RUN mkdir -p /data/mail /data/fts /data/logs /config/accounts /etc/dovecot

RUN chown -R vmail:vmail /data/mail /data/fts && \
    chown -R root:root /data/logs

EXPOSE 143 993

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /healthcheck.sh

VOLUME ["/config", "/data"]

ENTRYPOINT ["/entrypoint.sh"]
