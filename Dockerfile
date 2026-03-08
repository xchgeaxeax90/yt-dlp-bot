FROM python:3.13 AS builder

WORKDIR /build

RUN pip3 install "poetry"
COPY poetry.lock pyproject.toml /build/
RUN poetry install --no-root
COPY . /build/
RUN poetry build

FROM python:3.13-slim

RUN apt update && apt install -y ffmpeg && \
  apt clean all && rm -rf /var/lib/apt/lists*

RUN adduser --uid 1000 --gecos '' --gid 0 --disabled-password dl-bot && \
    mkdir -m 775 /opt/dl-bot && \
    chown -R 1000:0 /opt/dl-bot

ENV PATH="${PATH}:/home/dl-bot/.local/bin"

WORKDIR /opt/dl-bot
USER 1000

COPY --from=builder --chown=1000:0 /build/dist /opt/dl-bot/dist

RUN chown -R 1000:0 . && \
    chmod -R g=u . && \
    mv dist/*.tar.gz dist/yt_dlp_bot.tar.gz && \
    pip3 install --upgrade pip && \
    pip3 install dist/yt_dlp_bot.tar.gz && \
    rm -rf dist
