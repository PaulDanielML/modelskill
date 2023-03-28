import numpy as np
import pytest
import pandas as pd
import xarray as xr
import fmskill.comparison


def _get_df() -> pd.DataFrame:

    return df


def _set_attrs(data: xr.Dataset) -> xr.Dataset:
    data.attrs["variable_name"] = "fake var"
    data["x"].attrs["kind"] = "position"
    data["y"].attrs["kind"] = "position"
    data["Observation"].attrs["kind"] = "observation"
    data["Observation"].attrs["weight"] = 1.0
    data["Observation"].attrs["unit"] = "m"
    data["m1"].attrs["kind"] = "model"
    data["m2"].attrs["kind"] = "model"
    return data


@pytest.fixture
def pc() -> fmskill.comparison.Comparer:
    """A comparer with fake point data and 2 models"""
    x, y = 10.0, 55.0
    df = pd.DataFrame(
        {
            "Observation": [1.0, 2.0, 3.0, 4.0, 5.0, np.nan],
            "m1": [1.5, 2.4, 3.6, 4.9, 5.6, 6.4],
            "m2": [1.1, 2.2, 3.1, 4.2, 4.9, 6.2],
        },
        index=pd.date_range("2019-01-01", periods=6, freq="D"),
    )
    df.index.name = "time"
    raw_data = {"m1": df[["m1"]], "m2": df[["m2"]]}

    data = df.dropna().to_xarray()
    data.attrs["gtype"] = "point"
    data.attrs["name"] = "fake point obs"
    data["x"] = x
    data["y"] = y
    data = _set_attrs(data)
    return fmskill.comparison.Comparer(matched_data=data, raw_mod_data=raw_data)


@pytest.fixture
def tc() -> fmskill.comparison.Comparer:
    """A comparer with fake track data and 3 models"""
    df = pd.DataFrame(
        {
            "Observation": [-1.0, -2.0, -3.0, -4.0, -5.0, np.nan],
            "x": [10.1, 10.2, 10.3, 10.4, 10.5, 10.6],
            "y": [55.1, 55.2, 55.3, 55.4, 55.5, 55.6],
            "m1": [-1.5, -2.4, -3.6, -4.9, -5.6, -6.4],
            "m2": [-1.1, -2.2, -3.1, -4.2, -4.9, -6.2],
            "m3": [-1.3, -2.3, -3.3, -4.3, -5.3, -6.3],
        },
        index=pd.date_range("2019-01-03", periods=6, freq="D"),
    )
    df.index.name = "time"
    raw_data = {
        "m1": df[["x", "y", "m1"]],
        "m2": df[["x", "y", "m2"]],
        "m3": df[["x", "y", "m3"]],
    }

    data = df.dropna().to_xarray()
    data.attrs["gtype"] = "track"
    data.attrs["name"] = "fake track obs"
    data = _set_attrs(data)

    return fmskill.comparison.Comparer(matched_data=data, raw_mod_data=raw_data)


@pytest.fixture
def cc(pc, tc) -> fmskill.comparison.ComparerCollection:
    """A comparer collection with two comparers, with partial overlap in time
    one comparer with 2 models, one comparer with 3 models"""
    return fmskill.comparison.ComparerCollection([pc, tc])


def test_cc_properties(cc):
    assert cc.n_comparers == 2
    assert len(cc) == 2
    assert cc.n_models == 3  # first:2, second:3
    assert cc.n_points == 10  # 5 + 5
    assert cc.start == pd.Timestamp("2019-01-01")
    assert cc.end == pd.Timestamp("2019-01-07")
    assert cc.obs_names == ["fake point obs", "fake track obs"]
    assert cc.mod_names == ["m1", "m2", "m3"]


def test_cc_sel_model(cc):
    cc1 = cc.sel(model="m1")
    assert cc1.n_comparers == 2
    assert len(cc1) == 2
    assert cc1.n_models == 1
    assert cc1.n_points == 10
    assert cc1.start == pd.Timestamp("2019-01-01")
    assert cc1.end == pd.Timestamp("2019-01-07")
    assert cc1.obs_names == ["fake point obs", "fake track obs"]
    assert cc1.mod_names == ["m1"]


def test_cc_sel_model_m3(cc):
    cc1 = cc.sel(model="m3")
    assert cc1.n_comparers == 1
    assert len(cc1) == 1
    assert cc1.n_models == 1
