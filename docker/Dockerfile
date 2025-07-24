ARG UBUNTU_VERSION=22.04
ARG CUDA_VERSION=12.4.0
FROM ubuntu:$UBUNTU_VERSION AS base

# install essential packages
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        python3.10 \
        python3-pip \
        curl \
        ca-certificates \
        -y libglib2.0-0 libgl1-mesa-glx \
    	&& apt clean && rm -rf /var/lib/apt/lists/*

# install uv
ADD https://astral.sh/uv/0.6.17/install.sh /uv-installer.sh
RUN sh /sh uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"
COPY . /app/

# sync all requirements including optional ones
WORKDIR /app/.venv
RUN uv sync --frozen  --all-extras

# install the generated wheel for this app
RUN uv pip install sinapsis --extra-index-url https://pypi.sinapsis.tech


FROM nvidia/cuda:${CUDA_VERSION}-base-ubuntu$UBUNTU_VERSION AS nvidia-base
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        python3.10 \
        python3-pip \
        curl \
        ca-certificates \
        -y libglib2.0-0 libgl1-mesa-glx \
    	&& apt clean && rm -rf /var/lib/apt/lists/*


COPY --from=base /root/.local/bin /root/.local/bin
COPY --from=base /app/ /app/
ENV PATH="/root/.local/bin/:$PATH"
WORKDIR /app/.venv
