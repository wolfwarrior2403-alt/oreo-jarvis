FROM python:3.11-slim

# System deps: libsndfile for soundfile/librosa, ffmpeg for audio decoding,
# espeak-ng for pyttsx3's default Linux backend, build-essential for any
# source wheels that don't ship manylinux binaries.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        libsndfile1 \
        espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY pyproject.toml .

RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1 \
    OREO_ENV=production

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
