# see http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
# also see http://stackoverflow.com/questions/19926750/django-importerror-cannot-import-name-celery-possible-circular-import

from __future__ import absolute_import
# from django.apps import apps
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_projects.settings')

app = Celery('django_projects')
app.config_from_object('django.conf:settings')
# app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
