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

echo -e "${BLUE}========== Setting up local Python environment ==========${NC}"

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

echo -e "${BLUE}========== Changing directory to myproject ==========${NC}"
cd myproject || exit 1

echo -e "${BLUE}========== Initializing database ==========${NC}"
if (! try_python_command "init_db.py"); then
    echo -e "${RED}Error: Could not initialize database. Please check your Python installation.${NC}"
    exit 1
fi

echo -e "${BLUE}========== Running database migrations ==========${NC}"
if ( ! try_python_command "manage.py" "makemigrations"); then
    echo -e "${RED}Error: Could not run migrations. Please check your Python installation.${NC}"
    exit 1
fi

if (! try_python_command "manage.py" "migrate"); then
    echo -e "${RED}Error: Could not run migrations. Please check your Python installation.${NC}"
    exit 1
fi

echo -e "${BLUE}========== Creating admin team ==========${NC}"
if (! try_python_command "manage.py" "create_admin_team"); then
    echo -e "${RED}Error: Could not create admin team. Please check your Python installation.${NC}"
    exit 1
fi

echo -e "${BLUE}========== Starting development server ==========${NC}"
echo -e "${GREEN}The application will be available at http://127.0.0.1:8000/${NC}"
if (! try_python_command "manage.py" "runserver" "0.0.0.0:8000"); then
    echo -e "${RED}Error: Could not start development server. Please check your Python installation.${NC}"
    exit 1
fi
