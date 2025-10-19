ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.7
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apk add --no-cache python3 py3-pip python3-dev build-base     vlc bluez bluez-deprecated udev alsa-utils pulseaudio     tzdata git curl bash coreutils pkgconfig     py3-wheel py3-virtualenv     ttf-dejavu ttf-liberation

ARG BASHIO_VERSION=0.16.0
RUN curl -sSL -o /tmp/bashio.tar.gz https://github.com/hassio-addons/bashio/archive/v${BASHIO_VERSION}.tar.gz     && mkdir -p /usr/lib/bashio     && tar -xzf /tmp/bashio.tar.gz --strip 1 -C /usr/lib/bashio     && rm -f /tmp/bashio.tar.gz

WORKDIR /opt/skelly
COPY app/ /opt/skelly/

RUN python3 -m venv /opt/venv && source /opt/venv/bin/activate &&     pip install --upgrade pip setuptools wheel &&     pip install -r requirements.txt &&     ( [ -f requirements-additions.txt ] && pip install -r requirements-additions.txt || true )

COPY run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 8099
CMD [ "/run.sh" ]
