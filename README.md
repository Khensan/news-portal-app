# Capstone Project: News Portal Application

## How to Build and Run with Python venv
1. Initialize environment: python -m venv .venv
2. Activate environment: .\.venv\Scripts\Activate.ps1
3. Install project dependencies: pip install -r requirements.txt
4. Execute database structure routines: python manage.py migrate
5. Start development engine: python manage.py runserver

## How to Build and Run with Docker Container
1. Compile system layers: docker build -t news-app .
2. Run mapping the host bridge network: docker run -p 8000:8000 --add-host=host.docker.internal:host-gateway news-app
