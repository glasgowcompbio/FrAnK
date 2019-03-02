# FrAnK
A Fragment Annotation Kit for Mass Spectral Peaks

## Setup Guide
The following setup has been optimised for Ubuntu Desktop 18.04.2 LTS

### Running the Application
From a terminal, run the following commands:

```bash
sudo apt update
sudo apt install python-minimal python-pip libmysqlclient-dev libxml2-dev python-dev
pip install virtualenv
cd /home/<username>/projects
git clone https://github.com/glasgowcompbio/FrAnK.git
cd FrAnK
virtualenv env
source env/bin/activate
pipenv install PipFile --skip-lock
cd django_projects
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

N.B. This file was missing https://raw.githubusercontent.com/RonanDaly/pimp/master/venv/lib/python2.7/site-packages/pymzml/obo/psi-ms-4.0.1.obo
We need to fix this, the file is in the library when installed but is .obo.save

### Setting Up MySQL backend

Django comes pre-configured with sqlite3 as the default backend database for the application. 
However to allow for concurrent processing of background tasks, a development database is insufficient.
Whilst Django can support a variety of database technologies, the production system of FrAnK is supported by a backend mySQL database.

To set up the mySQL database with FrAnK, open a terminal and run the following:

```bash
sudo apt update
sudo apt-get install python-pip python-dev mysql-server libmysqlclient-dev
sudo mysql_secure_installation
```

When prompted, setup VALIDATE PASSWORD PLUGIN.
Set the desired level of password validation and set the root password.
Complete the setup, following the instructions and reload the privilege table upon completion.

Run the following commands in the shell:

```bash
systemctl status mysql
# If the service hasn't started automatically, then run...
systemctl start mysql
systemctl enable mysql
sudo /usr/bin/mysql -u root -p
```

Using the mysql command line tool, run the following:

```mysql
CREATE DATABASE frank CHARACTER SET UTF8;
CREATE USER frank@localhost IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON frank.* TO frank@localhost;
FLUSH PRIVILEGES;
exit
```

Open the file /home/_<username>_/projects/FrAnK/django_projects/django_projects/settings.py in the editor of your choice. 
Identify the configuration dict as below.

```python
# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
```

Replace the database configuration with the following:

```python
# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'frank',
        'USER': 'frank',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': ''
    }
}
```

Open a new terminal to test your new database configuration.

```bash
cd /home/<username>/projects/FrAnK/django_projects
source ../env/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Running Background Processing via Celery
From a second terminal, run the following:

```bash
export PYTHONPATH=/home/<user>/projects/FrAnK/django_projects
cd /home/<user>/projects/FrAnK
./run_celery.sh
``` 