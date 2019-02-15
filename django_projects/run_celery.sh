#!/bin/sh

# to be run inside the pipenv environment
if [ -z ${PIMP_CELERY_CONCURRENCY+x} ]; then
	exec celery worker;
else
	exec celery worker --concurrency ${PIMP_CELERY_CONCURRENCY};
fi

#!/bin/sh

DJANGO_SETTINGS_MODULE='django_projects.settings' celery -A frank worker -l info --max-tasks-per-child 20