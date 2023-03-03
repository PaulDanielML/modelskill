from typing import Union
import warnings

import xarray as xr
import mikeio
from fmskill.comparison import PointComparer, SingleObsComparer, TrackComparer

from fmskill.model import protocols, extraction
from fmskill.model._base import ModelResultBase
from fmskill.observation import PointObservation, TrackObservation


class GridModelResult(ModelResultBase):
    def extract(
        self, observation: Union[PointObservation, TrackObservation]
    ) -> protocols.Comparable:
        type_extraction_mapping = {
            (xr.Dataset, PointObservation): extraction.point_obs_from_xr_mr,
            (xr.Dataset, TrackObservation): extraction.track_obs_from_xr_mr,
            (mikeio.Dfs2, PointObservation): None,  # Possible future work
            (mikeio.Dfs2, TrackObservation): None,  # Possible future work
        }

        extraction_func = type_extraction_mapping.get(
            (type(self.data), type(observation))
        )
        if extraction_func is None:
            raise NotImplementedError(
                f"Extraction from {type(self.data)} to {type(observation)} is not implemented."
            )
        extraction_result = extraction_func(self, observation)

        return extraction_result

    def extract_observation(
        self, observation: Union[PointObservation, TrackObservation], validate=True
    ) -> SingleObsComparer:
        super().extract_observation(observation, validate)

        point_or_track_mr = self.extract(observation)
        if isinstance(observation, PointObservation):
            comparer = PointComparer(observation, point_or_track_mr.data)
        elif isinstance(observation, TrackObservation):
            comparer = TrackComparer(observation, point_or_track_mr.data)
        else:
            raise ValueError("Only point and track observation are supported!")

        if len(comparer.data) == 0:
            warnings.warn(f"No overlapping data in found for obs '{observation.name}'!")
            comparer = None

        return comparer


if __name__ == "__main__":
    grid_data = xr.open_dataset("tests/testdata/SW/ERA5_DutchCoast.nc")
    point_obs = PointObservation(
        "tests/testdata/SW/eur_Hm0.dfs0", item=0, x=3.2760, y=51.9990, name="EPL"
    )
    track_obs = TrackObservation(
        "tests/testdata/SW/Alti_c2_Dutch.dfs0", item=3, name="c2"
    )
    test = GridModelResult(grid_data, item="swh", name="test")

    assert isinstance(test, protocols.ModelResult)
    assert isinstance(test, protocols.Extractable)

    test.extract(point_obs)
    test.extract(track_obs)

    c1 = test.extract_observation(point_obs, validate=False)
    c2 = test.extract_observation(track_obs, validate=False)
