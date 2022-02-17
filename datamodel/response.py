from pydantic import BaseModel


class RossmannResponse(BaseModel):
    Id: int
    Sales: float
