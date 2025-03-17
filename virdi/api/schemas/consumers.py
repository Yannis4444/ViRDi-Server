from pydantic import BaseModel, Field


class ConsumerCreated(BaseModel):
    id: str = Field(..., description="The identifier of a consumer")
