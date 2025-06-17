import os

from dotenv import load_dotenv
from celery import Celery
from celery.schedules import crontab

# Database configuration
load_dotenv()
DATABASE_URL = os.getenv("PG_PSY_DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# Create Celery instance
reminders_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=f"db+{DATABASE_URL}",
    include=["tasks"],
)


@reminders_app.task
def create_reminders():
    print("Creating reminders...")
    pass


reminders_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    # Beat schedule configuration
    beat_schedule={
        "run-every-minute": {
            "task": "tasks.scheduled_task",
            "schedule": crontab(minute="*"),  # Execute every minute
        },
    },
)

# Optional: Configure task serialization
reminders_app.conf.task_serializer = "json"
reminders_app.conf.accept_content = ["json"]
reminders_app.conf.result_serializer = "json"
