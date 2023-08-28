# Noteworthy Backend

Django, MySQL and AWS Backend for [Noteworthy](https://www.github.com/dan-smith-tech/noteworthy) – an intuitive, productivity-enhancing, labour-reducing text editor built around Large Language Models and other AI tooling.

* See [noteworthy-frontend](https://github.com/jhels/noteworthy-frontend) for the associated frontend we're deploying.

* See [docs/architecture.md](docs/architecture.md) for design decisions.

* See [AWS/aws_readme.md](AWS/aws_readme.md) for details on how to deploy a LLaMA 2 model onto AWS using Terraform.

## Get Started - Development

### Set up MySQL Database

See [here](https://dev.mysql.com/doc/mysql-getting-started/en/) for the MySQL Getting Started docs, or follow the steps below.

* First, install MySQL – see [here](https://dev.mysql.com/doc/mysql-getting-started/en/#mysql-getting-started-installing) for download links and details.

* Check your MySQL installation works properly by logging in as root. In your terminal, run:
  ```bash
  mysql -u root -p
  ```
  and type in your root password.

* Now you're logged into MySQL, create a new superuser account as follows:
     ```SQL
     CREATE USER 'nw'@'localhost'            -- This is the username.
       IDENTIFIED BY 'JnlezOy`nC411"I}4S`Z'; -- This is the password.
     GRANT ALL
       ON *.*
       TO 'nw'@'localhost'
       WITH GRANT OPTION;
     
     exit -- Log out of root.
     ```
    
  * The username and password are chosen here to match the Django [settings.py](https://github.com/jhels/noteworthy-backend/blob/main/nw_backend/nw_backend/settings.py) configuration – see the `DATABASE` variable on line 79. We can and should change these later.

  * See [here](https://dev.mysql.com/doc/refman/8.0/en/creating-accounts.html#creating-accounts-granting-privileges) for more details on creating a superuser.

* Back in the terminal, run:
  ```bash
  mysql -u nw -p

  # nw is the username you set above.
  ```
  and enter the password above, ``JnlezOy`nC411"I}4S`Z``, to log into your newly created superuser account.

  Now you're inside MySQL, run:
  ```SQL
  CREATE DATABASE noteworthydb;
  ```
  * This name is also specified in the [settings.py](https://github.com/jhels/noteworthy-backend/blob/main/nw_backend/nw_backend/settings.py) `DATABASE` variable on line 79.
 
Well done! From this point on, we only need worry about Django and the code in this repo.
 
### Django and Server

* Set up and activate a Python virtual environment, and install the necessary packages.

    ```bash
    python venv path/to/your/venv
    source path/to/your/venv/bin/activate
    pip install django mysqlclient 
    ```

* Migrate the models in [models.py](https://github.com/jhels/noteworthy-backend/blob/main/nw_backend/user_accounts/models.py) to our newly created `noteworthydb` database:

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
    ```bash
    python nw_backend/manage.py runserver
    ```
    and visit the address it gives you - probably something like `http://127.0.0.1:8000/`.

* Visit `http://127.0.0.1:8000/admin` (or the equivalent if your local server's IP address is different) and enter the admin account details that you just made for the app. You should be able to view the Django administration page for the site.
 
Great job! You're all ready to start development on the site.
    
