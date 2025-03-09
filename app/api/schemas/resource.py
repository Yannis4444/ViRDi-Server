from pydantic import BaseModel, Field


class ProducedResource(BaseModel):
    amount: int = Field(..., description="The amount of the resource that was actually produced")

class ConsumedResource(BaseModel):
    amount: int = Field(..., description="The amount of the resource that was actually consumed")