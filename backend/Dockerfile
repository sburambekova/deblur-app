# The backend API. Build and run from backend/:
#   docker build -t deblur-backend .
#   docker run -p 8000:8000 -v deblur-data:/data deblur-backend
FROM python:3.13-slim

WORKDIR /app

# Dependencies first: this layer is rebuilt only when requirements.txt changes, not on every
# code change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# The database and the images. Mount a volume here, otherwise they are lost with the container.
ENV DEBLUR_DATA_DIR=/data
VOLUME /data

EXPOSE 8000
# sh -c so that $PORT set by a hosting is substituted (8000 if it is not set). exec replaces the
# shell with uvicorn, so uvicorn gets the stop signal and shuts down cleanly.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
