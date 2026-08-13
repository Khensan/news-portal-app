# Capstone Project: News Portal Application

## 🚀 Initial Repository Setup
Before building the application using a virtual environment or Docker, complete these initial setup steps:

### 1. Clone the Project Files
Open your terminal and clone the repository, then change directories into the project root:
```bash
git clone https://github.com
cd news-portal-app
```

### 2. Configure Local Environment Secrets
The application requires local configuration secrets to handle secure execution and database hooks. 
1. Create a file named `.env` in the root directory: `news-portal-app/.env`
2. Add your environment variables inside this file (adjust credentials to match your local setup):

```env
SECRET_KEY=your_secure_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Credentials
DB_NAME=news_portal_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

---

## How to Build and Run with Python venv
1. Initialize environment: python -m venv .venv
2. Activate environment: .\.venv\Scripts\Activate.ps1
3. Install project dependencies: pip install -r requirements.txt
4. Execute database structure routines: python manage.py migrate
5. Start development engine: python manage.py runserver

## How to Build and Run with Docker Container
1. Compile system layers: docker build -t news-app .
2. Run mapping the host bridge network: docker run -p 8000:8000 --env-file .env --add-host=host.docker.internal:host-gateway news-app
