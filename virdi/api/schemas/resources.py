from pydantic import BaseModel, Field


class ProduceResource(BaseModel):
    amount: int = Field(..., description="The amount of the resource that should be produced")
    resource_id: str = Field(..., description="The id of the resource to produce")

class ResourceProduced(BaseModel):
    amount: int = Field(..., description="The amount of the resource that was actually produced")

class ResourceConsumed(BaseModel):
    amount: int = Field(..., description="The amount of the resource that was actually consumed")