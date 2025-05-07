FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && \
    pip install --upgrade pip && \
    apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
