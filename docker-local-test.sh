#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========== Building ApplierPilotAI Docker Image ==========${NC}"
docker build -t applierpilotai .

echo -e "${BLUE}========== Running ApplierPilotAI Container ==========${NC}"
echo -e "${GREEN}The application will be available at http://localhost:8000/${NC}"
echo -e "${GREEN}Press Ctrl+C to stop the container${NC}"

docker run -p 8000:8000 applierpilotai 