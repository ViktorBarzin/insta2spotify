FROM python:3.13-slim

# apt-get upgrade pulls trixie-security fixes (libexpat1 and others) that the
# base image has not picked up yet.
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download easyocr model, then drop pip: nothing calls it at runtime, and
# its vendored urllib3, msgpack and setuptools carry High CVEs.
RUN python -c "import easyocr; easyocr.Reader(['en'], gpu=False)" \
    && pip uninstall -y pip

COPY . .

ENV DATABASE_PATH=/data/insta2spotify.db
VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
