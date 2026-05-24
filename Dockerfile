FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py ./
COPY modules ./modules
COPY static ./static

EXPOSE 9191

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9191"]
