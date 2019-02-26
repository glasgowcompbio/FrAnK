#!/bin/sh
export DJANGO_SETTINGS_MODULE='django_projects.settings'
# to be run inside the pipenv environment
if [ -z ${PIMP_CELERY_CONCURRENCY+x} ]; then
	exec celery -A django_projects worker -l info;
else
	exec celery -A django_projects worker -l info --max-tasks-per-child ${PIMP_CELERY_CONCURRENCY};
fi

#!/bin/sh
celery -A django_projects worker -l info --max-tasks-per-child 20
