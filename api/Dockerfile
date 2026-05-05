FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# for reading configs + curls to the esp32
RUN apt-get update && apt-get install -y \
    jq \                                                                                           
    curl \      
    openssh-client \
    && rm -rf /var/lib/apt/lists/*


COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

COPY . /app

EXPOSE 5055

ENTRYPOINT ["sh", "/app/api/tun.sh"]
