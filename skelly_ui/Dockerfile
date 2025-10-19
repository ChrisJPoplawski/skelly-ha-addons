ARG BUILD_FROM=ghcr.io/home-assistant/{arch}-base:latest
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apk add --no-cache \
    python3 py3-pip python3-dev build-base \
    vlc bluez udev alsa-utils pulseaudio tzdata git bash py3-virtualenv \
    ttf-dejavu ttf-liberation

WORKDIR /opt/skelly
COPY app/ /opt/skelly/

RUN python3 -m venv /opt/venv && . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    ( [ -f requirements-additions.txt ] && pip install -r requirements-additions.txt || true )

COPY run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 8099
CMD ["/run.sh"]
