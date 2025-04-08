#!/bin/bash

## Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========== Check if docker is running ==========${NC}"
docker ps > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}Docker is not running. Please start docker and try again.${NC}"
    exit 1
fi

echo -e "${BLUE}========== Stopping any running containers on port 8000 ==========${NC}"
CONTAINER_ID=$(docker ps | grep 8000 | awk '{print $1}')
if [ ! -z "$CONTAINER_ID" ]; then
    echo -e "${RED}Stopping container $CONTAINER_ID${NC}"
    docker kill $CONTAINER_ID
else
    echo -e "${GREEN}No running containers on port 8000${NC}"
fi

docker rm -f temp-container 2>/dev/null || true

echo -e "${BLUE}=========== Setting up environment ===========${NC}"

## see if we have a .env file lying around
if [ -f .env ]; then
    echo -e "${GREEN}Found .env file.${NC}"
    source .env
else
    echo -e "${RED}No .env file found. Assuming user knows what they're doing.${NC}"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}OPENAI_API_KEY environment variable is not set.${NC}"
    echo -e "${BLUE}Please enter your OpenAI API key:${NC}"
    read -s OPENAI_API_KEY
    export OPENAI_API_KEY
    
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}No API key provided. Features that use OpenAI may not work properly.${NC}"
    else
        echo -e "${GREEN}API key set for this session.${NC}"
    fi
else
    echo -e "${GREEN}Using OPENAI_API_KEY from environment.${NC}"
fi

echo -e "${BLUE}========== Generating SSL certificates for local testing ==========${NC}"
mkdir -p ./certs
if [ ! -f ./certs/key.pem ] || [ ! -f ./certs/cert.pem ]; then
    which openssl > /dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}OpenSSL not found. Please install it to generate certificates.${NC}"
        exit 1
    fi
    ## git bash being fucking awful
    MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:4096 -nodes \
        -out ./certs/cert.pem \
        -keyout ./certs/key.pem \
        -days 365 \
        -subj "/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
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

CERT_PATH=$(cd ./certs && pwd)

echo -e "${BLUE}========== Installing SSL certificates ==========${NC}"
docker create --name temp-container applierpilotai:latest
docker cp "${CERT_PATH}/cert.pem" temp-container:/app/ssl/cert.pem
docker cp "${CERT_PATH}/key.pem" temp-container:/app/ssl/key.pem
docker commit temp-container applierpilotai:latest
docker rm temp-container

echo -e "${BLUE}========== Running ApplierPilotAI Container ==========${NC}"

docker run -p 8000:8000 \
  -e "GUNICORN_CMD_ARGS=--timeout 120 --workers 2 --keyfile=/app/ssl/key.pem --certfile=/app/ssl/cert.pem --log-level debug" \
  -e "PRODUCTION=1" \
  -e "RUNNING_FROM_SCRIPT=1" \
  -e "OPENAI_API_KEY=$OPENAI_API_KEY" \
  applierpilotai:latest 