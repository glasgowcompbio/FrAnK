# FrAnK
A Fragment Annotation Kit for Mass Spectral Peaks

## Setup Guide
The following setup has been optimised for Ubuntu Desktop 18.04.2 LTS

From a terminal, run the following commands:
1. sudo apt install python-minimal python-pip libmysqlclient-dev libxml2-dev libxslt-dev python-dev
1. pip install virtualenv
1. cd into the directory you wish to run the application from
1. git clone https://github.com/glasgowcompbio/FrAnK.git
1. cd FrAnK
1. virtualenv env
1. source env/bin/activate
1. pip install pipenv
1. pipenv install PipFile --skip-lock
1. cd django_projects
1. python manage.py migrate
1. python manage.py createsuperuser
1. python manage.py runserver

1. N.B. This file was missing https://raw.githubusercontent.com/RonanDaly/pimp/master/venv/lib/python2.7/site-packages/pymzml/obo/psi-ms-4.0.1.obo