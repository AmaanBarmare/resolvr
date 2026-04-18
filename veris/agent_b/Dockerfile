FROM python:3.11-slim
WORKDIR /agent

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY risk_agent/ risk_agent/

ENV PYTHONUNBUFFERED=1
EXPOSE 8002

CMD ["python", "-m", "risk_agent.main"]
