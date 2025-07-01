"""
Example of how to add custom tracing to your FastAPI application
"""

from opentelemetry import trace
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import User

# Get the tracer for this module
tracer = trace.get_tracer(__name__)


# Example of adding custom tracing to an endpoint
@users_router.get("/{user_id}", response_model=Optional[UserResponseBase])
async def get_user_by_id_with_tracing(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> Optional[User]:
    # Create a custom span for this operation
    with tracer.start_as_current_span("get_user_by_id") as span:
        # Add attributes to the span
        span.set_attribute("user.id", user_id)
        span.set_attribute("operation.type", "read")

        # Add events to the span
        span.add_event("Starting user retrieval", {"user_id": user_id})

        try:
            service: BaseService[User, int, UserCreateRequest, UserCreateRequest] = (
                BaseService(User, session)
            )
            user = await service.get(user_id)

            # Add more attributes based on the result
            if user:
                span.set_attribute("user.found", True)
                span.set_attribute("user.email", user.email)
            else:
                span.set_attribute("user.found", False)

            span.add_event("User retrieval completed", {"user_found": user is not None})
            return user

        except Exception as e:
            # Record the error in the span
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            raise


# Example of tracing database operations
async def create_user_with_tracing(
    user_create_request: UserCreateRequest,
    session: AsyncSession,
) -> User:
    with tracer.start_as_current_span("create_user") as span:
        span.set_attribute("user.email", user_create_request.email)
        span.set_attribute("operation.type", "create")

        try:
            # This will be automatically traced by the psycopg instrumentation
            service: BaseService[User, int, UserCreateRequest, UserCreateRequest] = (
                BaseService(User, session)
            )
            user = await service.create(user_create_request)

            span.set_attribute("user.id", user.id)
            span.set_attribute("user.created", True)

            return user

        except Exception as e:
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            raise


# Example of tracing business logic
async def process_user_data(user_id: int, session: AsyncSession):
    with tracer.start_as_current_span("process_user_data") as span:
        span.set_attribute("user.id", user_id)

        # Create child spans for different operations
        with tracer.start_as_current_span("fetch_user_data") as fetch_span:
            fetch_span.set_attribute("operation", "fetch_user_data")
            # Your fetch logic here
            pass

        with tracer.start_as_current_span("validate_user_data") as validate_span:
            validate_span.set_attribute("operation", "validate_user_data")
            # Your validation logic here
            pass

        with tracer.start_as_current_span("save_user_data") as save_span:
            save_span.set_attribute("operation", "save_user_data")
            # Your save logic here
            pass
