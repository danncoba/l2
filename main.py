from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from routers.analytics import analytics_router
from routers.configs import config_router
from routers.grades import grades_router
from routers.matrix import matrix_router
from routers.matrix_chats import matrix_chats_router
from routers.notifications import notifications_router
from routers.profile import profile_router
from routers.skills import skills_router
from routers.testing import testing_router
from routers.users import users_router

from logger import logger
from telemetry import setup_telemetry, instrument_fastapi
from utils.tracing import TraceIdMiddleware

load_dotenv()
# Setup OpenTelemetry tracing
setup_telemetry()

logger.info("Starting application...")

app = FastAPI(
    title="Morpheus @ HTEC",
    description="""Morpheus @ HTEC helps engineers populate and validate their skill matrix.
        Application will remind the engineers, that still have not populated entire matrix, or have some
        unpopulated fields to populate these fields accordingly.
        """,
)

origins = [
    "http://localhost:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TraceIdMiddleware)

app.include_router(profile_router)
app.include_router(users_router)
app.include_router(grades_router)
app.include_router(notifications_router)
app.include_router(config_router)
app.include_router(skills_router)
app.include_router(matrix_router)
app.include_router(matrix_chats_router)
app.include_router(analytics_router)
app.include_router(testing_router)

# Instrument FastAPI with OpenTelemetry
instrument_fastapi(app)
