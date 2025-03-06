#!/bin/bash

## Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========== Installing coverage package ===========${NC}"
## other pips cause fucking issues
if(command -v pip3 &> /dev/null); then
    pip3 install coverage
elif(command -v pip &> /dev/null); then
    pip install coverage
else
    echo -e "${RED}Error: Could not find pip or pip3. Please install pip first.${NC}"
    exit 1
fi

echo -e "${BLUE}=========== Running tests with coverage ===========${NC}"
cd myproject

## Try different ways of running coverage
if(command -v python3 &> /dev/null); then
    python3 -m coverage run --source='.' manage.py test
elif(command -v python &> /dev/null); then
    python -m coverage run --source='.' manage.py test
else
    echo -e "${RED}Error: Could not find python or python3. Please check your Python installation.${NC}"
    exit 1
fi

echo -e "${BLUE}=========== Coverage Report ===========${NC}"
if(command -v python3 &> /dev/null); then
    python3 -m coverage report
else
    python -m coverage report
fi

echo -e "${BLUE}=========== Generating HTML Coverage Report ===========${NC}"
if(command -v python3 &> /dev/null); then
    python3 -m coverage html
else
    python -m coverage html
fi

echo -e "${GREEN}Done! HTML coverage report available in htmlcov/index.html${NC}"
echo -e "${BLUE}Open it with your browser to see detailed coverage information${NC}" 