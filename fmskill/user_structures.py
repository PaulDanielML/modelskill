from typing import Optional, Union
import warnings

from fmskill import types
from fmskill.data_container import DataContainer, compare


class Observation:
    def __new__(
        self,
        data: types.DataInputType,
        item: types.ItemSpecifier = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        name: Optional[str] = None,
    ) -> DataContainer:

        return DataContainer(
            data=data,
            item=item,
            is_observation=True,
            x=x,
            y=y,
            name=name,
        )


class ModelResult:
    def __new__(
        self,
        data: types.DataInputType,
        item: types.ItemSpecifier = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        name: Optional[str] = None,
    ) -> DataContainer:

        return DataContainer(
            data=data,
            item=item,
            is_result=True,
            x=x,
            y=y,
            name=name,
        )


ObservationIndex = int
ModelResultIndex = int


class Comparer:
    def __init__(
        self,
        observations: Union[Observation, list[Observation]],
        results: Union[ModelResult, list[ModelResult]],
    ) -> None:

        self.observations = []
        self.results = []
        self.extracted = {}

        self.observation_names = set()
        self.result_names = set()

        if not isinstance(observations, list):
            observations = [observations]
        if not isinstance(results, list):
            results = [results]

        self._add_data(observations + results)

    def __getitem__(self, key):
        if not self.extracted:
            warnings.warn("No data extracted. Use Comparer.extract() first.")
            return

        if isinstance(key, str):
            if key in self.extracted:
                return self.extracted[key]

            else:
                partial_matches = [
                    k for k in self.extracted.keys() if key.lower() in k.lower()
                ]
                if len(partial_matches) > 1:
                    return {k: self.extracted[k] for k in partial_matches}
                elif len(partial_matches) == 1:
                    return self.extracted[partial_matches[0]]

        elif isinstance(key, int):
            if key < len(self.extracted):
                return list(self.extracted.values())[key]
            elif -len(self.extracted) < key < 0:
                return list(self.extracted.values())[key + len(self.extracted)]
            else:
                raise IndexError(f"Index out of range: {key}")

    def _add_data(self, data: list[Union[ModelResult, Observation, "Comparer"]]):
        for d in data:
            if isinstance(d, DataContainer):
                if d.is_observation:
                    if d.name in self.observation_names:
                        warnings.warn(
                            f"Duplicate observation name: {d.name}. Please choose unique names."
                        )
                    else:
                        self.observations.append(d)
                elif d.is_result:
                    if d.name in self.result_names:
                        warnings.warn(
                            f"Duplicate result name: {d.name}. Please choose unique names."
                        )
                    else:
                        self.results.append(d)
            elif isinstance(d, Comparer):
                self._add_data(d.observations + d.results)
            else:
                raise ValueError(f"Unknown data type: {type(d)}")

        # _comparison_idc: list[
        #     tuple[ModelResultIndex, ObservationIndex]
        # ] = DataContainer.check_compatibility(self.results + self.observations)

        # Tuples of valid comparisons, format: (result_index, observation_index)
        # self._pair_idc = [(m, o - len(self.results)) for m, o in _comparison_idc]

    def extract(self):
        """
        Build a dictionary of extracted data, using the names of the
        observations and results as keys.
        """

        compare(self.results + self.observations)

        for i_m, i_o in self._pair_idc:
            identifier = f"{self.results[i_m].name} - {self.observations[i_o].name}"
            if identifier not in self.extracted:
                self.extracted[identifier] = self.results[i_m].compare(
                    self.observations[i_o]
                )

        print("hold")

    def plot_observation_positions(self, title=None, figsize=None):
        from fmskill.plot import plot_observation_positions

        res_idc_with_geom = [
            i for i, r in enumerate(self.results) if r.geometry is not None
        ]
        if not res_idc_with_geom:
            warnings.warn("Only supported for dfsu ModelResults")
            return

        return plot_observation_positions(
            self.results[res_idc_with_geom[0]].geometry,
            self.observations,
            title=title,
            figsize=figsize,
        )

    def plot_temporal_coverage(
        self,
        *,
        show_model=True,
        limit_to_model_period=True,
        marker="_",
        title=None,
        figsize=None,
    ):

        from fmskill.plot import plot_temporal_coverage

        return plot_temporal_coverage(
            modelresults=self.results if show_model else [],
            observations=self.observations,
            limit_to_model_period=limit_to_model_period,
            marker=marker,
            title=title,
            figsize=figsize,
        )


if __name__ == "__main__":
    fldr = "tests/testdata/SW/"
    o1 = Observation(fldr + "HKNA_Hm0.dfs0", item=0, x=4.2420, y=52.6887, name="HKNA")
    o2 = Observation(fldr + "eur_Hm0.dfs0", item=0, x=3.2760, y=51.9990, name="EPL")
    o3 = Observation(fldr + "Alti_c2_Dutch.dfs0", item=3, name="c2")

    mr1 = ModelResult(fldr + "HKZN_local_2017_DutchCoast.dfsu", name="SW_1", item=0)
    mr2 = ModelResult(fldr + "HKZN_local_2017_DutchCoast_v2.dfsu", name="SW_2", item=0)

    c = Comparer([o1, o2, o3], [mr1, mr2])

    c.extract()

    print("hold")
