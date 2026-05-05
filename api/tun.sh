#!/bin/sh

set -x

CLARK_IP=$(cat /app/config/config.json |  jq -r ".CLARK_IP")

SSH_KEY=/app/ssh_key
SSH_KNOWN_HOSTS=/app/known_hosts

CLARK_PORT=5055
BLE_PORT=5055

CLARK_HOST=sce@${CLARK_IP}

open_ssh_tunnel () {
    ssh \
    -o UserKnownHostsFile=${SSH_KNOWN_HOSTS} \
    -o StrictHostKeyChecking=no \
    -i ${SSH_KEY} \
    -f -g -N -R 0.0.0.0:${CLARK_PORT}:localhost:${BLE_PORT} ${CLARK_HOST}
}

chmod 600 ${SSH_KEY}

# setup the esp_ip in the env
export ESP_IP=$(cat /app/config/config.json |  jq -r ".ESP_IP")

open_ssh_tunnel
exec uvicorn api.test_server:app --host 0.0.0.0 --port 5055
