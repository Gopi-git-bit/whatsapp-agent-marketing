# Web App Backend

This repository contains a reference implementation of a backend service for a modern web application.  It demonstrates how to combine several production‑grade technologies together:

* **Django** for the core web framework.
* **Django REST Framework** for building JSON APIs.
* **JWT (JSON Web Token)** authentication via `djangorestframework‑simplejwt`.
* **Celery** with **Redis** for asynchronous task processing.
* **Django Channels** with **Redis** for WebSocket support.
* **PostgreSQL** (or another relational database) for persistent data storage.
* **Sentry** for error monitoring.
* A custom middleware demonstrating how to enforce an SLA (service level agreement) by recording request latencies.

> ⚠️ **Note:** The code in this repository is intended as a template and may require adjustments for your specific environment.  The dependencies listed in `requirements.txt` must be installed in your Python environment for the application to run.  You will also need running Redis and PostgreSQL instances for the asynchronous and database features, respectively.

## Quickstart

1.  Install the Python dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2.  Create a `.env` file at the project root and configure environment variables as needed.  At a minimum you should specify the database connection, Redis URL and JWT settings.  See `backend/settings.py` for the environment variables used.

3.  Apply the database migrations:

    ```bash
    python manage.py migrate
    ```

4.  Run a local development server:

    ```bash
    python manage.py runserver
    ```

5.  Start a Celery worker and the beat scheduler in separate terminals:

    ```bash
    celery -A backend worker --loglevel=info
    celery -A backend beat --loglevel=info
    ```

6.  Run the Channels server (which uses ASGI instead of WSGI):

    ```bash
    python manage.py runserver 0.0.0.0:8000
    ```

7.  Visit `http://localhost:8000/api/` to explore the REST API endpoints.

See the inline comments throughout the code for more details on how each component fits together.
