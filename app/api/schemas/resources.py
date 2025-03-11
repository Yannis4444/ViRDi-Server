from pydantic import BaseModel, Field


class ResourceProduced(BaseModel):
    amount: int = Field(..., description="The amount of the resource that was actually produced")

class ResourceConsumed(BaseModel):
    amount: int = Field(..., description="The amount of the resource that was actually consumed")