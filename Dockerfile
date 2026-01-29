FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

# Persist order_counts.json (use a volume in production)
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
