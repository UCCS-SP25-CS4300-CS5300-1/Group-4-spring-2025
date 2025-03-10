#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========== Stopping any running containers on port 8000 ==========${NC}"
CONTAINER_ID=$(docker ps | grep 8000 | awk '{print $1}')
if [ ! -z "$CONTAINER_ID" ]; then
    echo -e "${RED}Stopping container $CONTAINER_ID${NC}"
    docker kill $CONTAINER_ID
else
    echo -e "${GREEN}No running containers on port 8000${NC}"
fi

echo -e "${BLUE}========== Generating SSL certificates for local testing ==========${NC}"
mkdir -p ./certs
if [ ! -f ./certs/key.pem ] || [ ! -f ./certs/cert.pem ]; then
    which openssl > /dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}OpenSSL not found. Please install it to generate certificates.${NC}"
        exit 1
    fi
    openssl req -x509 -newkey rsa:4096 -nodes -out ./certs/cert.pem -keyout ./certs/key.pem -days 365 -subj "/CN=localhost"
    echo -e "${GREEN}Self-signed certificates generated in ./certs/${NC}"
else
    echo -e "${GREEN}Using existing certificates in ./certs/${NC}"
fi

echo -e "${BLUE}========== Building ApplierPilotAI Docker Image ==========${NC}"
docker build -t applierpilotai:latest .

echo -e "${BLUE}========== Running ApplierPilotAI Container ==========${NC}"
echo -e "${GREEN}The application will be available at https://localhost:8000/${NC}"
echo -e "${RED}NOTE: Browser security warnings are expected since we're using a self-signed certificate${NC}"
echo -e "${GREEN}Press Ctrl+C to stop the container${NC}"

docker run -p 8000:8000 \
  -v "$(pwd)/certs/key.pem:/app/key.pem" \
  -v "$(pwd)/certs/cert.pem:/app/cert.pem" \
  -e "GUNICORN_CMD_ARGS=--timeout 120 --workers 2 --keyfile=/app/key.pem --certfile=/app/cert.pem --log-level debug" \
  -e "PRODUCTION=1" \
  applierpilotai:latest 