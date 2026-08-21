# Capstone Project: News Portal Application

A robust, enterprise-grade Django web application and REST API designed to manage and distribute news content. The platform enforces strict business rules around content ownership, content delivery, and user role management to ensure reliable editorial publishing lifecycles.

---

## 🚀 Key Features

* **Exclusive Content Ownership Pattern**: Enforces strict validation rules where an `Article` must be explicitly owned by either an independent journalist or a corporate publisher, but never both simultaneously.
* **Dynamic Role Management**: Automatic synchronization of user groups and structural permissions through custom database lifecycle signals.
* **RESTful Endpoints**: Dedicated API layer for content retrieval, including optimized endpoints like `get_latest_news`.
* **Comprehensive Database Migrations**: Fully tracked transactional schema revisions using modular migration states.
* **Automated Test Suite**: Built-in unit and integration tests verifying API schema responses, model validation constraints, and business logic.
* **Auto-generated Documentation**: Fully pre-configured Sphinx build engine to extract docstrings directly from classes, models, and endpoints into clean HTML references.

---

## 🛠️ Technologies Used

| Technology Layer | Tooling Selection | Functional Responsibility |
| :--- | :--- | :--- |
| **Language Runtime** | Python 3.10+ | Core processing engine & backend scripts |
| **Web Framework** | Django 4.2+ / 5.0 | Application ecosystem & Object-Relational Mapping (ORM) |
| **API Architecture** | Django REST Framework (DRF) | REST endpoint serialization and content delivery |
| **Database Engine** | PostgreSQL | Enterprise relational storage and transactional indexing |
| **Container Framework** | Docker | Environment isolation and infrastructure packaging |
| **Documentation Builder** | Sphinx | Docstring parsing and interactive HTML output generation |

---

## ⚙️ Initial Repository Setup

Before building the application using a virtual environment or Docker, complete these initial configuration setups:

### 1. Clone the Project Files
Open your terminal and clone the repository, then change directories into the project root:
```bash
git clone https://github.com
cd news-portal-app
```

### 2. Configure Local Environment Secrets
> ⚠️ **Critical Security Requirement**: Create a local `.env` configuration payload inside your root system path: `news-portal-app/.env`.

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

## 💻 Local Environment Deployment Strategies

Choose **one** of the two environment deployment orchestration tracks detailed below:

### Track A: Bare-Metal Execution via Python `venv`

<details>
<summary>📦 Click to expand local python virtual environment setup instructions</summary>

#### 1. Initialize the Environment
```bash
python -m venv .venv
```

#### 2. Activate the Isolated Environment
* **Windows (PowerShell)**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
* **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
* **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

#### 3. Install Project Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Execute Database Structure Routines
Apply migrations to build your local PostgreSQL schemas:
```bash
python manage.py migrate
```

#### 5. Start the Development Engine
```bash
python manage.py runserver
```
Access the application portal locally at: `http://127.0.0.1:8000/`
</details>

### Track B: Isolated Containerization via Docker

<details>
<summary>🐳 Click to expand containerized Docker setup instructions</summary>

#### 1. Compile System Layers
```bash
docker build -t news-app .
```

#### 2. Run Mapping the Host Bridge Network
```bash
docker run -p 8000:8000 --env-file .env --add-host=host.docker.internal:host-gateway news-app
```
</details>
### Track B: Isolated Containerization via Docker

<details open>
<summary>🐳 Click to expand containerized Docker setup instructions</summary>

Ensure you have **Docker Desktop** and **Docker Compose** installed on your system before proceeding.

#### 1. Configure the Environment
Ensure your local `.env` file is fully configured in the root directory. To run your database inside Docker alongside the application, change your `DB_HOST` variable to match the database service name:
```env
DB_HOST=db
```

#### 2. Build and Launch Infrastructure
Run the following command to build the project images and spin up the multi-container environment (Django application and PostgreSQL database) in detached background mode:
```bash
docker compose up --build -d
```

#### 3. Run Database Migrations
Execute the Django schema migration routines directly inside your active application container:
```bash
docker compose exec web python manage.py migrate
```

#### 4. Verify System Services
Check the live tracking status of your running container architecture:
```bash
docker compose ps
```
Once verified, access the operational application portal locally at: `http://localhost:8000/`

#### 5. Useful Runtime Lifecycle Commands
* **View application logs:** `docker compose logs -f`
* **Stop container ecosystem:** `docker compose down`
* **Execute test workflows:** `docker compose exec web python manage.py test`
</details>

---

## 🧪 Verification & Automated Testing

The integrated test suite checks business validations—including the mutually exclusive article ownership constraints—to guarantee stability:

```bash
# Ensure your environment track is fully active prior to executing
python manage.py test
```

---

## 📂 Project Directory Structure

```text
news-portal-app/
│
├── manage.py                # Root application controller and admin wrapper
├── requirements.txt         # Package dependencies register
├── .env                     # Local environment keys configuration file
├── Dockerfile               # Container layer orchestration build script
├── README.md                # System documentation setup and guidelines
│
├── news_project/            # Global Project Orchestration Package
│   ├── __init__.py
│   ├── asgi.py              # Asynchronous execution gateway configuration
│   ├── settings.py          # Core settings matrix and security contexts
│   ├── urls.py              # Root routing nexus and path dispatchers
│   └── wsgi.py              # Synchronous WSGI web server container hook
│
├── news_api/                # Core Functional API Application Core
│   ├── __init__.py
│   ├── admin.py             # Django Admin site model registrations
│   ├── apps.py              # Module registry configurations
│   ├── models.py            # Article models & lifecycle signal definitions
│   ├── views.py             # Content endpoints and request/response views
│   ├── urls.py              # App-level routing patterns
│   └── migrations/          # Database Progression Records
│       ├── __init__.py
│       └── 0001_initial.py  # Initial migration node
│
└── docs/                    # Automated Sphinx Documentation Suite
    ├── conf.py              # Sphinx compilation configuration
    ├── index.rst            # Root documentation tree map
    ├── modules.rst          # Module file pointers index
    └── _build/              # Rendered compilation output folder
        └── html/            # Human-readable local web assets
```

---

## 📡 API Usage Profiles

### 1. Retrieve the Latest News Coverage
* **Endpoint**: `/api/news/latest/`
* **HTTP Method**: `GET`

#### Success Schema (`200 OK`)
```json
[
  {
    "id": 1,
    "title": "Local Investigative Report",
    "content": "Detailed text body covering local regulatory compliance frameworks...",
    "pub_date": "2026-08-19T12:00:00Z",
    "author_type": "independent_journalist"
  }
]
```

---

### 2. Creating an Article (Enforced Constraints)
> ❗ **Validation Rule Enforced**: You must supply either a valid `journalist_id` or a `publisher_id`. Submitting values for both fields or leaving both blank returns a validation failure code (`400 Bad Request`).

* **Endpoint**: `/api/news/articles/`
* **HTTP Method**: `POST`

#### Payload Schema Contract
```json
{
  "title": "Breaking Tech Update",
  "content": "System documentation compiled cleanly.",
  "journalist_id": 4,
  "publisher_id": null
}
```

---

## 📖 Compiling System Documentation

Whenever system docstrings or API path decorators change, compile the updated output references cleanly with Sphinx:

```bash
# Navigate to the documentation workspace folder
cd docs

# Wipe previous builds and regenerate static HTML pages
make html
```

The compiled assets are stored directly in your local directory tree at `docs/_build/html/`. Double-click **`index.html`** within that directory to load the responsive, searchable documentation interface directly inside your web browser.
