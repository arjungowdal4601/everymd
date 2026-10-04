FROM node:24.13.0-bookworm-slim
ENV HYPERFRAMES_NO_TELEMETRY=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg chromium unzip fonts-liberation fonts-dejavu-core ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN npm install --global hyperframes@0.8.121
WORKDIR /project
