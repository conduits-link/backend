# Noteworthy Backend

Django and MySQL Backend for [Noteworthy](https://www.github.com/dan-smith-tech/noteworthy) – an intuitive, productivity-enhancing text editor based around Large Language Models and other AI tooling.

See [docs/architecture.md](docs/architecture.md) for design decisions.

## Get Started - Development

### Set up MySQL Database

See [here](https://dev.mysql.com/doc/mysql-getting-started/en/) for the MySQL Getting Started docs.

* First, install MySQL – see [here](https://dev.mysql.com/doc/mysql-getting-started/en/#mysql-getting-started-installing) for download links and details.

* Check your MySQL installation works properly by logging in as root. In your terminal, run:
  ```
  mysql -u root -p
  ```
  and type in your root password.

* Now you're logged into MySQL, create a new superuser account as follows:
     ```
     CREATE USER 'nw'@'localhost'
       IDENTIFIED BY 'JnlezOy`nC411"I}4S`Z';
     GRANT ALL
       ON *.*
       TO 'nw'@'localhost'
       WITH GRANT OPTION;
     ```
    
  * The username and password are chosen here to match the Django [settings.py](https://github.com/jhels/noteworthy-backend/blob/main/nw_backend/nw_backend/settings.py) configuration - see the `DATABASE` variable on line 79. We can and should change these later.

  * See [here](https://dev.mysql.com/doc/refman/8.0/en/creating-accounts.html#creating-accounts-granting-privileges) for more details on creating a superuser.

* Create the database `noteworthydb` as follows. In terminal – not logged into MySQL – run:
  ```
  mysql -u nw -p
  ```
  and enter the password above, `JnlezOy`nC411"I}4S`Z`, to log into your newly created superuser account. Then run:
  ```
  CREATE DATABASE noteworthydb;
  ```
  * This name is also specified in the settings.py `DATABASE` variable.
 
Well done! From this point on, we only need worry about Django and the code in this repo.
 
### Django and Server

* Set up and activate a Python virtual environment, and install the necessary packages.

    ```python
    python venv path/to/your/venv
    source path/to/your/venv/bin/activate
    pip install django mysqlclient 
    ```

* Migrate the models in [models.py](https://github.com/jhels/noteworthy-backend/blob/main/nw_backend/user_accounts/models.py) to our `noteworthydb` database:

    ```bash
    python nw_backend/manage.py makemigrations
    python nw_backend/manage.py migrate
    ```
  * You'll need to run these commands again if you change any of the models in `models.py`.
 
* Make an admin account for the app:
  ```bash
  python nw_backend/manage.py createsuperuser
  ```
  and enter a username, email and password.

* Run the development web server:
    ```
    python nw_backend/manage.py runserver
    ```
    and visit the address it gives you - probably something like `http://127.0.0.1:8000/`.
  * If you visit `http://127.0.0.1:8000/admin` and enter your application superuser details you'll be able to view the Django administration page for the site.
 
Great job! You're all ready to start development on the site.
    
