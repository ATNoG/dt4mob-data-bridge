from typing import Iterator, List

from geopy.distance import geodesic
from pydantic import BaseModel, Field, RootModel


class Point(BaseModel, frozen=True):
    longitude: float = Field(alias="x")
    latitude: float = Field(alias="y")

    def to_tuple(self) -> tuple[float, float]:
        return self.longitude, self.latitude


class PolyLine(RootModel[List[Point]]):
    # HACK: PolyLine must behave like line, not tuple(str, Any). This causes a
    # conflict with the default behaviour of BaseModel, hence the type error
    def __iter__(self) -> Iterator[Point]:  # ty:ignore[invalid-method-override]
        return iter(self.root)

    def __getitem__(self, index: int) -> Point:
        return self.root[index]

    def __len__(self) -> int:
        return len(self.root)

    def length(self) -> int:
        return len(self.root)
