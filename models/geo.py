from pydantic import BaseModel, Field, RootModel
from geopy.distance import geodesic
from typing import List


class Point(BaseModel, frozen=True):
    longitude: float = Field(alias="x")
    latitude: float = Field(alias="y")

    def to_tuple(self) -> tuple[float, float]:
        return self.longitude, self.latitude


class PolyLine(RootModel[List[Point]]):
    def length(self) -> int:
        return len(self.root)

    def point_length(self) -> List[float]:
        dists = [0.0]
        dists.extend(
            [
                geodesic(p1.to_tuple(), p2.to_tuple()).meters
                for p1, p2 in zip(self.root[:-1], self.root[1:])
            ]
        )
        return dists

    def split_line(self, segment_distance: float = 100) -> List["PolyLine"]:
        if len(self.root) <= 1:
            return [PolyLine(root=self.root)] if self.root else []

        result: List[PolyLine] = []
        current_points: List[Point] = [self.root[0]]
        current_length = 0.0  # length of current segment

        for p1, p2 in zip(self.root[:-1], self.root[1:]):
            # Remaining distance in this polyline segment (p1 -> p2)
            remaining_seg_start = p1

            while True:
                seg_len = geodesic(remaining_seg_start.to_tuple(), p2.to_tuple()).meters

                # If this segment fits entirely into the current polyline chunk
                if current_length + seg_len <= segment_distance:
                    current_points.append(p2)
                    current_length += seg_len
                    break  # move to next original segment

                # Need to cut somewhere between remaining_seg_start and p2
                remaining_to_fill = segment_distance - current_length
                if seg_len == 0:
                    # Degenerate case: points too close
                    break

                # Fraction along the remaining segment where we reach the limit
                frac = remaining_to_fill / seg_len

                # Linear interpolation in lon/lat
                cut_lon = remaining_seg_start.longitude + frac * (
                    p2.longitude - remaining_seg_start.longitude
                )
                cut_lat = remaining_seg_start.latitude + frac * (
                    p2.latitude - remaining_seg_start.latitude
                )
                cut_point = Point(x=cut_lon, y=cut_lat)

                # Close current polyline at cut_point
                current_points.append(cut_point)
                result.append(PolyLine(root=current_points))

                # Start a new polyline from cut_point
                current_points = [cut_point]
                current_length = 0.0

                # Now continue along the remaining part of the original segment
                remaining_seg_start = cut_point

        # Add the last accumulated segment if it has more than one point
        if len(current_points) > 1:
            result.append(PolyLine(root=current_points))

        return result
