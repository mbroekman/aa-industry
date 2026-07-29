"""
App Models
"""

# Third Party

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _


class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        """Meta definitions"""

        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app"),
            ("corp_access", "Can access corporate industry jobs"),
            (
                "industrialist_access",
                "Can access the industrialist dashboard and claim jobs",
            ),
        )


class TaskExecutionLog(models.Model):
    STATUS_CHOICES = (
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("RUNNING", "Running"),
    )
    task_name = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="RUNNING")
    last_run = models.DateTimeField(auto_now=True)
    duration_seconds = models.FloatField(default=0.0)
    message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Task Execution Log")
        verbose_name_plural = _("Task Execution Logs")

    def __str__(self):
        return f"{self.task_name} - {self.status}"
