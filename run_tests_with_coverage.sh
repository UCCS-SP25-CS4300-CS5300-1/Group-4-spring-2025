#!/bin/bash

## Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

try_python_command() {
    local cmd=$1
    shift
    if (command -v py &> /dev/null); then
        py $cmd "$@"
        return $?
    elif (command -v python3 &> /dev/null); then
        python3 $cmd "$@"
        return $?
    elif (command -v python &> /dev/null); then
        python $cmd "$@"
        return $?
    else
        python $cmd "$@"
        return $?
    fi
    return 1
}

echo -e "${BLUE}=========== Installing coverage package ===========${NC}"
if (command -v pip3 &> /dev/null); then
    pip3 install -r requirements.txt
elif (command -v pip &> /dev/null); then
    pip install -r requirements.txt
else
    echo -e "${RED}Error: Could not find pip or pip3. Please install pip first.${NC}"
    exit 1
fi

echo -e "${BLUE}=========== Running tests with coverage ===========${NC}"
cd myproject

if (! try_python_command "-m" "coverage" "run" "--source=." "manage.py" "test"); then
    echo -e "${RED}Error: Could not find Python. Please check your Python installation.${NC}"
    exit 1
fi

echo -e "${BLUE}=========== Coverage Report ===========${NC}"
if (! try_python_command "-m" "coverage" "report"); then
    echo -e "${RED}Error: Failed to generate coverage report.${NC}"
    exit 1
fi

echo -e "${BLUE}=========== Generating HTML Coverage Report ===========${NC}"
if (! try_python_command "-m" "coverage" "html"); then
    echo -e "${RED}Error: Failed to generate HTML coverage report.${NC}"
    exit 1
fi

echo -e "${GREEN}Done! HTML coverage report available in htmlcov/index.html${NC}"
echo -e "${BLUE}Open it with your browser to see detailed coverage information${NC}"