# Conduit Backend

Django, MySQL and AWS Backend for [Conduit](https://github.com/conduits-link/core) – an intuitive, productivity-enhancing, labour-reducing text editor built around Large Language Models and other AI tooling.

* See [AWS/aws_readme.md](AWS/aws_readme.md) for details on how to deploy a LLaMA 2 model onto AWS using Docker and Terraform.

## Contents

* [Get Started - Development](#get-started---development)
  * [Set up MySQL Database](#set-up-mysql-database)
  * [Django and Server](#django-and-server-setup)
  * [Testing](#testing)

## Get Started - Local Development

### Set up MySQL Database

If you want to test offline, you can do so with MySQL by following the instructions below.

See [here](https://dev.mysql.com/doc/mysql-getting-started/en/) for the MySQL Getting Started docs, or follow the steps below.

* First, install MySQL and set up your root account – see [here](https://dev.mysql.com/doc/mysql-getting-started/en/#mysql-getting-started-installing) for download links and details.

* Inside this directory, run:
    ```bash
    pip install mysqlclient
    ```

* Check your MySQL installation works properly by logging in as root. In your terminal, run:
  ```bash
  mysql -u root -p
  ```
  and type in your root password, set in the step above.

* Now you're logged into MySQL, set up a new superuser account as follows:
     ```SQL
     CREATE USER 'conduit'@'localhost'            -- This is the username.
       IDENTIFIED BY 'JnlezOynC411I4SZ'; -- This is the password.
     GRANT ALL
       ON *.*
       TO 'conduit'@'localhost'
       WITH GRANT OPTION;

     GRANT ALL PRIVILEGES ON test_conduitdb.* TO 'conduit'@'localhost'; -- Allows us to run Django tests later.
     
     exit; -- Log out of root.
     ```
    
  * The username and password are chosen here to match the Django [settings.py](/conduit_backend/settings.py) configuration – see the "MySQL local database for testing" comment. We can and should change these later.

  * See [here](https://dev.mysql.com/doc/refman/8.0/en/creating-accounts.html#creating-accounts-granting-privileges) for more details on creating a superuser.

* Back in the terminal, run:
  ```bash
  mysql -u nw -p

  # nw is the username you set above.
  ```
  and enter the password above -
  ```
  JnlezOy`nC411"I}4S`Z
  ```
  \- to log into your newly created superuser account.

  Now you're inside MySQL, run:
  ```SQL
  CREATE DATABASE conduitdb;
  ```
  * This name is also specified in the [settings.py](https://github.com/jhels/conduit-backend/blob/main/conduit_backend/conduit_backend/settings.py) `DATABASE` variable on line 79.
 
Well done! From this point on, we only need worry about Django and the code in this repo.
 
### Django and Server Setup

* Set up and activate a Python virtual environment, and install the necessary packages.

    ```bash
    python venv path/to/your/venv
    source path/to/your/venv/bin/activate
    conda activate # if using conda
    pip install -r requirements.txt
    ```

* Uncomment the "MySQL local database for testing" code in [settings.py](/conduit_backend/settings.py). Migrate the models in [models.py](/user_accounts/models.py) to our newly created `conduitdb` database:

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
    
### Testing

All features of the site should have associated test functions in `user_accounts/tests.py`.

To run them, simply call:
```
python manage.py test
```
