import logging

from django.core.management.base import BaseCommand

from ...models import Job


logger = logging.getLogger(__name__)


def handle_jobs():
    jobs = Job.objects.filter(
        is_enabled=True,
        status=Job.STATUS_SCHEDULED,
    )

    for job in jobs:
        try:
            job.handle()
        except Exception as e:
            logger.exception('JOB HANDLING ERROR:')
            job.status = Job.STATUS_ERROR
            job.error_message = str(e)
            update_fields = {'status', 'error_message'}
        else:
            job.status = Job.STATUS_DONE
            update_fields = {'status'}

        job.save(update_fields=update_fields)


class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        handle_jobs()
