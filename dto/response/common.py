from openai import BaseModel


class ActionSuccessResponse(BaseModel):
    success: bool
    message: str
