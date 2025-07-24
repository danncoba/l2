import os

import dotenv
from celery import Celery
from celery.schedules import crontab

env_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), ".env"
)
dotenv.load_dotenv(env_file)

app = Celery("sample_project", broker="redis://localhost:6379/0")


app.conf.update(
    result_backend="redis://localhost:6379/0",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        # "send-matrix-validations-every-minute": {
        #     "task": "tasks.create_matrix_validations",
        #     "schedule": crontab(minute="*"),  # Alternative: using crontab every minute
        #     "args": (
        #         "sms",
        #         {"phone_number": "1234567890", "message": "Scheduled SMS notification"},
        #     ),
        # },
        "send-test-supervisor-matrix-validations-every-minute": {
            "task": "tasks.generate_matrix_validation_questions",
            "schedule": crontab(minute="*"),  # Alternative: using crontab every minute
            "args": (),
        },
    },
)

import tasks
