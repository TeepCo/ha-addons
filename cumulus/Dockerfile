ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy root filesystem
COPY rootfs /

# Copy Python requirements file
COPY requirements.txt /tmp/

# Set workdir
WORKDIR /opt

# Setup base
RUN \
    apk add --no-cache --virtual .build-dependencies \
      gcc \
      libc-dev \
      linux-headers \
    \
    && apk add --no-cache \
      libffi-dev \
      autossh \
    \
    && pip3 install -r /tmp/requirements.txt \
    && python3 -m compileall cumulus \
    \
    && chmod 700 /root/.ssh \
    && chmod 600 /root/.ssh/config \
    \
    && apk del --no-cache --purge .build-dependencies \
    && rm -fr \
        /root/.cache \
        /tmp/*

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Hejki <https://github.com/hejki>" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="TeepCo" \
    org.opencontainers.image.authors="Hejki <https://github.com/hejki>" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://teepco.cz" \
    org.opencontainers.image.source="https://github.com/TeepCo/ha-addons/tree/main/cumulus" \
    org.opencontainers.image.documentation="https://github.com/TeepCo/ha-addons/blob/main/cumulus/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}
