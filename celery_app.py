from celery import Celery
from celery.schedules import crontab

app = Celery("sample_project", broker="redis://localhost:6379/0")

app.conf.update(
    result_backend="redis://localhost:6379/0",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        "send-matrix-validations-every-minute": {
            "task": "tasks.create_matrix_validations",
            "schedule": crontab(minute="*"),  # Alternative: using crontab every minute
            "args": (
                "sms",
                {"phone_number": "1234567890", "message": "Scheduled SMS notification"},
            ),
        },
    },
)

import tasks
