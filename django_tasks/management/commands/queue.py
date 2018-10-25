import logging

from django.core.management.base import BaseCommand

from ...models import Task


logger = logging.getLogger(__name__)


def handle_tasks():
    tasks = Task.objects.filter(
        is_enabled=True,
        status=Task.STATUS_SCHEDULED,
    )

    for task in tasks:
        try:
            task.handle()
        except Exception as e:
            logger.exception('TASK HANDLING ERROR:')
            task.status = Task.STATUS_ERROR
            task.error_message = str(e)
            update_fields = {'status', 'error_message'}
        else:
            task.status = Task.STATUS_DONE
            update_fields = {'status'}

        task.save(update_fields=update_fields)


class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        handle_tasks()
