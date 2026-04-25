FROM docker.arvancloud.ir/python:3.9-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app


COPY . /app/
COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


# CMD ["python", "-u", "bot.py"]
