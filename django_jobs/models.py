from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation,
)
from django.contrib.contenttypes.models import ContentType


__all__ = [
    'JobMakerMixin',
    'Job',
]


class Job(models.Model):

    STATUS_CREATED = 0
    STATUS_SCHEDULED = 1
    STATUS_STARTED = 2
    STATUS_STOPPED = 3
    STATUS_RESTARTED = 4
    STATUS_CANCELED = 5
    STATUS_ERROR = 6
    STATUS_DONE = 7
    STATUS_CHOICES = [
        (STATUS_CREATED, 'CREATED'),
        (STATUS_SCHEDULED, 'SCHEDULED'),
        (STATUS_STARTED, 'STARTED'),
        (STATUS_STOPPED, 'STOPPED'),
        (STATUS_RESTARTED, 'RESTARTED'),
        (STATUS_CANCELED, 'CANCELED'),
        (STATUS_ERROR, 'ERROR'),
        (STATUS_DONE, 'DONE'),
    ]

    EXTRA_STATUS_TO_RESTART = 0
    EXTRA_STATUS_TO_CANCEL = 1
    EXTRA_STATUS_CHOICES = [
        (EXTRA_STATUS_TO_RESTART, 'TO_RESTART'),
        (EXTRA_STATUS_TO_CANCEL, 'TO_CANCEL'),
    ]

    created = models.DateTimeField(verbose_name='created at', editable=False)
    modified = models.DateTimeField(verbose_name='modified at', editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    maker_object = GenericForeignKey('content_type', 'object_id')
    handler_id = models.IntegerField(
        verbose_name='handler id',
        blank=True,
        null=True,
    )
    is_enabled = models.BooleanField(verbose_name='is enabled', default=True)
    status = models.PositiveSmallIntegerField(
        verbose_name='status',
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        db_index=True,
    )
    extra_status = models.PositiveSmallIntegerField(
        verbose_name='extra status',
        choices=EXTRA_STATUS_CHOICES,
        db_index=True,
        blank=True,
        null=True,
    )
    error_message = models.TextField(
        verbose_name='error message',
        blank=True,
    )

    class Meta:
        verbose_name = 'job'
        verbose_name_plural = 'jobs'

    def __str__(self):
        return 'Job - %s' % self.created

    def handle(self):
        self.maker_object.handle_job(self.handler_id)

    def save(self, *args, **kwargs):
        now = timezone.now()

        if not self.id:
            self.created = now

        self.modified = now
        super(Job, self).save(*args, **kwargs)


class JobMakerMixin(models.Model):

    _job_handlers = None

    jobs = GenericRelation(Job)

    class Meta:
        abstract = True

    @classmethod
    def register_job_handler(cls, handler, handler_id, handler_name):
        if cls._job_handlers is None:
            cls._job_handlers = dict()

        cls._job_handlers[handler_id] = dict(
            handler=handler,
            name=handler_name,
        )

        return handler

    def get_handler_name(self, handler_id):
        return self._job_handlers[handler_id]['name'].upper() or handler_id

    def create_job(self, handler_id):
        return self.jobs.get_or_create(
            handler_id=handler_id,
            status=Job.STATUS_CREATED,
            defaults=dict(
                maker_object=self,
            ),
        )

    def schedule_job(self, handler_id):
        return self.jobs.get_or_create(
            handler_id=handler_id,
            status__in=(
                Job.STATUS_CREATED,
                Job.STATUS_SCHEDULED,
                Job.STATUS_STARTED,
                Job.STATUS_RESTARTED,
                Job.STATUS_STOPPED,
                Job.STATUS_DONE,
            ),
            defaults=dict(
                maker_object=self,
                status=Job.STATUS_SCHEDULED,
            ),
        )

    def handle_job(self, handler_id):
        return self._job_handlers[handler_id]['handler'](self)
