FROM python:3.11-slim
WORKDIR /agent

COPY requirements.txt .
RUN uv install --no-cache-dir -r requirements.txt

COPY revenue_agent/ revenue_agent/

