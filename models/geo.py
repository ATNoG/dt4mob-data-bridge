from pydantic import BaseModel, Field


class Point(BaseModel):
    longitude: float = Field(alias="x")
    latitude: float = Field(alias="y")
