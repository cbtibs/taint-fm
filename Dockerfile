# hadolint global ignore=DL3008
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 
ENV WORKDIR=/app
ENV DISCORD_TOKEN=${DISCORD_TOKEN}

RUN groupadd -g 1000 bot && useradd -m -u 1000 -g bot bot

WORKDIR $WORKDIR
RUN chown -R bot:bot $WORKDIR

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=bot:bot . .

USER bot

ENTRYPOINT ["python", "bot.py"]
