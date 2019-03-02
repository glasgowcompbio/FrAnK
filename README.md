# FrAnK
A Fragment Annotation Kit for Mass Spectral Peaks

## Setup Guide
The following setup has been optimised for Ubuntu Desktop 18.04.2 LTS

### Running the Application
From a terminal, run the following commands:

```bash
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

### Running Background Processing via Celery
From a second terminal, run the following:

```bash
export PYTHONPATH=/home/<user>/projects/FrAnK/django_projects
cd /home/<user>/projects/FrAnK
./run_celery.sh
``` 