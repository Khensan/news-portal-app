# 📰 News Portal Web Application & REST API

A complete Django-based news publishing system featuring a reader-facing HTML template interface, an automated editorial moderation workflow dashboard, and a robust Django REST Framework (DRF) API backend.

---

## 🛠️ Option 1: Local Deployment with Virtual Environment (venv)

Follow these steps to run the application natively on your host machine using Python's built-in virtual environment runner.

### Prerequisite Tracking
* Python 3.11 or higher installed on your system.
* Pip package manager active.

### Execution Blueprint

1. **Navigate to the Project Root Folder:**
   ```bash
   cd news_project
   ```

2. **Initialize and Activate Virtual Environment:**
   ```bash
   # Windows PowerShell:
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux Terminal:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install django djangorestframework requests sphinx sphinx-rtd-theme
   ```

4. **Synchronize Database State Engines:**
   ```bash
   python manage.py makemigrations news_api
   python manage.py migrate
   ```

5. **Create an Administrative Editor Profile:**
   ```bash
   python manage.py createsuperuser
   ```
   *(Ensure you log into Django Admin at `/admin/` after booting up to set your user's `role` field metadata string to `EDITOR` so you can pass dashboard permission checks).*

6. **Boot the Local Network Engine:**
   ```bash
   python manage.py runserver
   ```
   * Access the public reader homepage interface at: `http://127.0.0`
   * Access the editorial dashboard workspace at: `http://127.0.0dashboard/`

---

## 🐳 Option 2: Isolated Deployment with Docker

Follow these steps to deploy the application inside an isolated container ecosystem. This guarantees the project works uniformly across different host computers without separate dependency configurations.

### Prerequisite Tracking
* Docker Desktop installed and running.

### Execution Blueprint

1. **Navigate to the Project Root Directory (where Dockerfile sits):**
   ```bash
   cd news_project
   ```

2. **Build and Boot the Container Workspace:**
   Run the orchestration layout utility to automatically build the isolated image layers, link network bridge ports, and execute database schemas:
   ```bash
   docker-compose up --build
   ```

3. **Create an Administrative Editor Account (Inside Container Shell):**
   Open a separate terminal window while the container is actively running and run the superuser utility straight inside the isolated instance:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Access the Application Suite:**
   * Public Reader Template Homepage: `http://127.0.0`
   * Secure Editorial Moderation Queue Dashboard: `http://127.0.0dashboard/`
   * Core Engine REST API Landing Node: `http://127.0.0api/`

5. **Spin Down Container Operations:**
   Press `CTRL + C` in your running shell window, or run this command to safely terminate the instance paths:
   ```bash
   docker-compose down
   ```

---

## 📚 Viewing Technical Documentation (Sphinx Manual)
An interactive technical user manual built from backend docstrings is bundled with this repository. To view the codebase layout structure:
1. Navigate to your computer's local folder tree: `..\news_project\docs\html\`
2. Double-click the file named **`index.html`** to open the cross-referenced guide right inside any standard web browser.
