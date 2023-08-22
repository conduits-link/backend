# Noteworthy Backend

Backend for [Noteworthy](https://github.com/dan-smith-tech/noteworthy).

See [docs/architecture.md](docs/architecture.md) for design decisions.

## Get Started - Development Server

* Install MySQL - see [here](https://dev.mysql.com/doc/mysql-installation-excerpt/5.7/en/installing.html).

* Set up and activate a Python virtual environment:

    ```python
    python venv path/to/your/venv
    source path/to/your/venv/bin/activate
    ```

* Install the necessary packages to your virtual environment.

    ```bash
    pip install django mysqlclient 
    ```

* If you've edited any model fields, migrate these changes:

    ```bash
    python nw_backend/manage.py makemigrations
    python nw_backend/manage.py migrate
    ```

* Run the development web server:
    ```
    python manage.py runserver
    ```
    
