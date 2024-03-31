# Conduit Backend

Django, MySQL and AWS Backend for [Conduit](https://github.com/conduits-link/core) – an intuitive, productivity-enhancing, labour-reducing text editor built around Large Language Models and other AI tooling.

* See [AWS/aws_readme.md](AWS/aws_readme.md) for details on how to deploy a LLaMA 2 model onto AWS using Docker and Terraform.

* See [docs/architecture.md](docs/architecture.md) for design.

## Django and Server Setup

* Set up and activate a Python virtual environment, and install the necessary packages.

    ```bash
    python venv path/to/your/venv
    source path/to/your/venv/bin/activate
    conda activate # if using conda
    pip install -r requirements.txt
    ```

* Migrate the models in [models.py](/user_accounts/models.py) to our newly created `conduitdb` database:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```
  * You'll need to run these commands again if you change any of the models in `models.py`.
 
* Make an admin account for the app:
  ```bash
  python manage.py createsuperuser
  ```
  and enter a username, email and password.

* Run the development web server:
    ```bash
    python manage.py runserver
    ```
    and visit the address it gives you - probably something like `http://127.0.0.1:8000/`.

* Visit `http://127.0.0.1:8000/admin` (or the equivalent if your local server's IP address is different) and enter the admin account details that you just made for the app. You should be able to view the Django administration page for the site.
 
Great job! You're all ready to start development on the site.
    
## Testing

All features of the site should have associated test functions in `user_accounts/tests.py`.

To run them, simply call:
```
python manage.py test
```
