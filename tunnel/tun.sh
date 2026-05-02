#!/bin/sh

SSH_KEY=/app/ssh/id_rsa
SSH_KNOWN_HOSTS=/app/ssh/known_hosts
API_PORT=5055

if [ -z "$CORE_V4_IP" ]; then
    echo "ERROR: CORE_V4_IP environment variable is not set"
    exit 1
fi

chmod 600 ${SSH_KEY}

echo "Opening reverse SSH tunnel: sce@${CORE_V4_IP}:${API_PORT} -> api:${API_PORT}"

exec ssh \
    -o UserKnownHostsFile=${SSH_KNOWN_HOSTS} \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -i ${SSH_KEY} \
    -N -R ${API_PORT}:api:${API_PORT} \
    sce@${CORE_V4_IP}
