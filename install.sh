#!/bin/bash

# Set color variables for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Check if pip is installed
if ! command_exists pip3; then
    echo -e "${RED}pip is not installed. Please install pip first.${NC}"
    exit 1
fi

# Check if virtualenv is installed, if not, install it
if ! command_exists virtualenv; then
    echo -e "${YELLOW}Virtualenv not found. Installing...${NC}"
    pip3 install virtualenv
fi

# Project setup function
setup_django_project() {
    # Create virtual environment
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m virtualenv venv

    # Activate virtual environment
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate

    # Install requirements
    echo -e "${GREEN}Installing project dependencies...${NC}"
    pip install -r requirements.txt

    # Check if Django is installed
    if ! pip freeze | grep -q Django; then
        echo -e "${YELLOW}Django not found in requirements. Installing Django...${NC}"
        pip install django
    fi

    # Run migrations
    echo -e "${GREEN}Running database migrations...${NC}"
    python manage.py migrate

    # Collect static files
    echo -e "${GREEN}Collecting static files...${NC}"
    python manage.py collectstatic --noinput

    # Create .env file if it doesn't exist (optional)
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file with default settings...${NC}"
        cat > .env << EOL
DEBUG=True
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///db.sqlite3
EOL
    fi

    echo -e "${GREEN}Project setup complete!${NC}"
}

# Run server function
run_server() {
    # Activate virtual environment if not already active
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi

    # Run Django development server
    echo -e "${GREEN}Starting Django development server...${NC}"
    python manage.py runserver
}

# Main script
clear
echo -e "${YELLOW}Django Project Setup and Run Script${NC}"

# Check if script is running in a Django project
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: This script must be run in a Django project root directory.${NC}"
    exit 1
fi

# Main menu
while true; do
    echo -e "\nChoose an option:"
    echo "1. Setup Project"
    echo "2. Run Server"
    echo "3. Create Superuser"
    echo "4. Exit"
    read -p "Enter your choice (1-4): " choice

    case $choice in
        1)
            setup_django_project
            ;;
        2)
            run_server
            ;;
        3)
            python manage.py createsuperuser
            ;;
        4)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            ;;
    esac
done