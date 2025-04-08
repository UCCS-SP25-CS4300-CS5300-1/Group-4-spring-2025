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

echo -e "${BLUE}=========== Setting up environment ===========${NC}"

## see if we have a .env file lying around
if [ -f .env ]; then
    echo -e "${GREEN}Found .env file.${NC}"
    source .env
else
    echo -e "${RED}No .env file found. Assuming user knows what they're doing.${NC}"
fi


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

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}OPENAI_API_KEY environment variable is not set.${NC}"
    echo -e "${BLUE}Please enter your OpenAI API key:${NC}"
    read -s OPENAI_API_KEY
    export OPENAI_API_KEY
    
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}No API key provided. Tests that use OpenAI may fail.${NC}"
    else
        echo -e "${GREEN}API key set for this session.${NC}"
    fi
else
    echo -e "${GREEN}Using OPENAI_API_KEY from environment.${NC}"
fi

## utility scripts and migrations that aren't releveant to testing
if (! try_python_command "-m" "coverage" "run" "--source=." "--omit=config.py,init_db.py,users/management/commands/create_admin_team.py,apply.py,*/migrations/*,*/tests/*,*/test_*.py,manage.py,config-*.py" "manage.py" "test"); then
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