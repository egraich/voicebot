FROM mwader/static-ffmpeg:7.1.0 AS ffmpeg

FROM python:3.11-slim

WORKDIR /app

COPY --from=ffmpeg /ffmpeg /usr/local/bin/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "main.py"]