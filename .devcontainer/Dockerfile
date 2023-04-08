FROM ghcr.io/home-assistant/devcontainer:addons

ARG PYTHON_VERSION

RUN \
    apt-get update \
    && apt-get install -y libffi-dev autossh \
    \
    && cd /tmp \
    && curl https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz > python.tgz \
    && ls -al \
    && tar -xvf python.tgz \
    && cd Python-${PYTHON_VERSION} \
    && ./configure --enable-optimizations \
    && make -j 4 \
    && make altinstall


# && apt-get install -y python3-distutils  \
# && curl https://bootstrap.pypa.io/get-pip.py > /tmp/get-pip.py \
# && python3 /tmp/get-pip.py

# && pip3 install -r /workspaces/ha-addons/cumulus/requirements.txt