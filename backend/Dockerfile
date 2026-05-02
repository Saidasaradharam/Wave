FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
# This upgrade is the key to fixing your build error
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
EXPOSE 8080
CMD uvicorn main:app --host 0.0.0.0 --port $PORT