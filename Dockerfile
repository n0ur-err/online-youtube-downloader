FROM python:3.11-slim

# Install system deps: Node.js 20 LTS + ffmpeg + curl
RUN apt-get update && apt-get install -y --no-install-recommends curl ffmpeg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# bgutil PO-token server (Node.js)
RUN npm install -g @ybd-project/bgutil-ytdlp-pot-provider

# yt-dlp plugin that makes yt-dlp talk to the bgutil server automatically
RUN mkdir -p /root/.config/yt-dlp/plugins/bgutil/yt_dlp_plugins/extractor \
    && curl -fsSL \
    "https://raw.githubusercontent.com/ybd-project/bgutil-ytdlp-pot-provider/main/plugins/ytdlp/bgutil-ytdlp-pot-provider.py" \
    -o /root/.config/yt-dlp/plugins/bgutil/yt_dlp_plugins/extractor/bgutil_pot_provider.py

# App source
COPY . .
RUN mkdir -p downloads

EXPOSE 5000
CMD ["bash", "docker_start.sh"]
