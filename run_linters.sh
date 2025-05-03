#!/bin/bash

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
    echo -e "${RED}No .env file found. Assuming environment variables are set manually.${NC}"
fi

## First, install dependencies including linters
echo -e "${BLUE}=========== Installing/Updating Packages ===========${NC}"
if (command -v pip3 &> /dev/null); then
    pip3 install -r requirements.txt
elif (command -v pip &> /dev/null); then
    pip install -r requirements.txt
else
    echo -e "${RED}Error: Could not find pip or pip3. Please install pip first.${NC}"
    exit 1
fi

echo -e "${BLUE}=========== Running Linting Checks ===========${NC}"
mkdir -p linting_reports

export PYTHONPATH=$PYTHONPATH:$(pwd)

## This helps with pylint, since pylint needs a __init__.py file in the root directory, but we don't do imports in the package style
echo -e "${BLUE}Creating temporary __init__.py for linting...${NC}"
touch myproject/__init__.py

echo -e "${BLUE}Running PyLint checks...${NC}"
if (! try_python_command "-m" "pylint" "myproject" "--output-format=text:linting_reports/pylint_report.txt,colorized"); then
    echo -e "${RED}Warning: PyLint found some issues.${NC}"
fi

if [ -f linting_reports/pylint_report.txt ]; then
    PYLINT_SCORE=$(tail -n 2 linting_reports/pylint_report.txt | grep -oP "(?<=rated at )[0-9.]+")
    if [ ! -z "$PYLINT_SCORE" ]; then
        echo -e "${BLUE}PyLint Score: ${PYLINT_SCORE}${NC}"
        if awk -v score="$PYLINT_SCORE" 'BEGIN { exit !(score < 7.0) }'; then
            echo -e "${RED}Warning: PyLint score is below 7.0. Please review the code quality.${NC}"
        fi
    fi
fi

echo -e "${GREEN}Linting reports available in:${NC}"
echo -e "${BLUE}- PyLint Report: linting_reports/pylint_report.txt${NC}"

## Import will break if we have a __init__.py file in the root directory
echo -e "${BLUE}Removing temporary __init__.py...${NC}"
rm -f myproject/__init__.py

echo -e "${GREEN}Linting script finished.${NC}" 