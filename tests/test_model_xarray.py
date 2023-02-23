import sys
from datetime import datetime
import pytest
import xarray as xr
import pandas as pd

import mikeio

import fmskill
from fmskill.model import ModelResult

# from fmskill.model import XArrayModelResultItem
from fmskill.observation import PointObservation, TrackObservation
from fmskill.comparison import PointComparer, TrackComparer

python3_7_or_above = pytest.mark.skipif(
    sys.version_info < (3, 7), reason="requires Python3.7+"
)


@pytest.fixture
def ERA5_DutchCoast_nc():
    return "tests/testdata/SW/ERA5_DutchCoast.nc"


@pytest.fixture
def mr_ERA5_pp1d(ERA5_DutchCoast_nc):
    return ModelResult(ERA5_DutchCoast_nc, item="pp1d")


@pytest.fixture
def mr_ERA5_swh(ERA5_DutchCoast_nc):
    return ModelResult(ERA5_DutchCoast_nc, item="swh")


@pytest.fixture
def mf_modelresult():
    fn = "tests/testdata/SW/CMEMS_DutchCoast_*.nc"
    # ds = xr.open_mfdataset(fn)
    return ModelResult(fn, item="VHM0", name="CMEMS")


@pytest.fixture
def pointobs_epl_hm0():
    return PointObservation(
        "tests/testdata/SW/eur_Hm0.dfs0", item=0, x=3.2760, y=51.9990, name="EPL"
    )


@pytest.fixture
def trackobs_c2_hm0():
    return TrackObservation("tests/testdata/SW/Alti_c2_Dutch.dfs0", item=3, name="c2")


def test_XArrayModelResult_from_nc(mr_ERA5_pp1d):
    mr = mr_ERA5_pp1d

    assert isinstance(mr, XArrayModelResultItem)
    # assert isinstance(mr.data, xr.Dataset)     # maybe better to have an attribute data which could then be a DataArray or something else---
    assert "ERA5_DutchCoast.nc" in mr.filename
    # assert "- Item: 4: swh" in repr(mr)
    # assert len(mr) == 5
    # assert len(mr.data) == 5
    assert mr.name == "ERA5_DutchCoast"
    assert mr.item_name == "pp1d"
    assert mr.start_time == datetime(2017, 10, 27, 0, 0, 0)
    assert mr.end_time == datetime(2017, 10, 29, 18, 0, 0)
    assert mr.itemInfo == mikeio.ItemInfo(mikeio.EUMType.Undefined)


def test_XArrayModelResult_from_DataArray(ERA5_DutchCoast_nc):
    ds = xr.open_dataset(ERA5_DutchCoast_nc)
    mr = ModelResult(ds["swh"])

    assert isinstance(mr, XArrayModelResultItem)
    # assert isinstance(mr.data, xr.DataArray)
    assert mr.item_name == "swh"
    assert not mr.filename
    assert mr.itemInfo == mikeio.ItemInfo(mikeio.EUMType.Undefined)


def test_XArrayModelResult_from_da(ERA5_DutchCoast_nc):
    ds = xr.open_dataset(ERA5_DutchCoast_nc)
    da = ds["swh"]
    mr = ModelResult(da)

    assert isinstance(mr, XArrayModelResultItem)
    assert not mr.filename


def test_XArrayModelResult_from_multifile(mf_modelresult):
    mr = mf_modelresult

    assert isinstance(mr, XArrayModelResultItem)
    # assert isinstance(mr.data, xr.DataArray)   # maybe better to have an attribute data which could then be a DataArray or something else---
    assert "CMEMS_DutchCoast_*.nc" in mr.filename
    assert mr.name == "CMEMS"
    assert mr.start_time == datetime(2017, 10, 28, 0, 0, 0)
    assert mr.end_time == datetime(2017, 10, 29, 18, 0, 0)


# no longer supported
# def test_XArrayModelResult_select_item(modelresult):
#     mr = modelresult

#     assert isinstance(mr["mwd"], XArrayModelResultItem)
#     assert isinstance(mr[0], XArrayModelResultItem)


# should be supported
def test_XArrayModelResultItem(ERA5_DutchCoast_nc):
    mri1 = ModelResult(ERA5_DutchCoast_nc, item="pp1d")
    assert isinstance(mri1, XArrayModelResultItem)

    mri2 = ModelResult(ERA5_DutchCoast_nc, item=3)
    assert isinstance(mri2, XArrayModelResultItem)

    assert mri1.name == mri2.name
    assert mri1._selected_item == mri2._selected_item  # do we still need this?


def test_XArrayModelResultItem_itemInfo(ERA5_DutchCoast_nc):
    mri1 = ModelResult(ERA5_DutchCoast_nc, item="pp1d")
    assert mri1.itemInfo == mikeio.ItemInfo(mikeio.EUMType.Undefined)

    itemInfo = mikeio.EUMType.Wave_period
    mri3 = ModelResult(ERA5_DutchCoast_nc, item="pp1d", itemInfo=itemInfo)
    mri3.itemInfo == mikeio.ItemInfo(mikeio.EUMType.Wave_period)

    itemInfo = mikeio.ItemInfo("Peak period", mikeio.EUMType.Wave_period)
    mri3 = ModelResult(ERA5_DutchCoast_nc, item="pp1d", itemInfo=itemInfo)
    mri3.itemInfo == mikeio.ItemInfo("Peak period", mikeio.EUMType.Wave_period)


def test_XArrayModelResult_getitem(mr_ERA5_pp1d):
    mri = mr_ERA5_pp1d

    assert "XArrayModelResultItem" in repr(mri)
    assert "- Item: pp1d" in repr(mri)
    assert isinstance(mri.data, xr.Dataset)
    # assert len(mri) == 1   # has no length (it's an item)
    assert len(mri.data) == 1  # Keep this?
    assert mri.name == "ERA5_DutchCoast"
    assert mri.item_name == "pp1d"


# should we test "private" methods?
def test_XArrayModelResult_extract_point(mr_ERA5_swh, pointobs_epl_hm0):
    df = mr_ERA5_swh._extract_point(pointobs_epl_hm0)
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 1
    assert pytest.approx(df.iloc[0, 0]) == 0.875528


@python3_7_or_above
def test_XArrayModelResultItem_validate_point(mf_modelresult, pointobs_epl_hm0):
    mri = mf_modelresult

    ok = mri._validate_start_end(pointobs_epl_hm0)
    assert ok


def test_XArrayModelResultItem_extract_point(mr_ERA5_swh, pointobs_epl_hm0):
    pc = mr_ERA5_swh.extract_observation(pointobs_epl_hm0)
    df = pc.data

    assert isinstance(pc, PointComparer)
    assert pc.start == datetime(2017, 10, 27, 0, 0, 0)
    assert pc.end == datetime(2017, 10, 29, 18, 0, 0)
    assert pc.n_models == 1
    assert pc.n_points == 67
    assert pc.n_variables == 1
    assert len(df.dropna()) == 67


def test_XArrayModelResultItem_extract_point_xoutside(mr_ERA5_pp1d, pointobs_epl_hm0):
    mri = mr_ERA5_pp1d
    pointobs_epl_hm0.x = -50
    with pytest.warns(UserWarning, match="Cannot add zero-length modeldata"):
        pc = mri.extract_observation(pointobs_epl_hm0)

    assert pc == None


def test_XArrayModelResultItem_extract_point_toutside(
    ERA5_DutchCoast_nc, pointobs_epl_hm0
):
    ds = xr.open_dataset(ERA5_DutchCoast_nc)
    da = ds["swh"].isel(time=slice(10, 15))
    da["time"] = pd.Timedelta("365D") + da.time
    mr = ModelResult(da)
    with pytest.warns(UserWarning, match="No overlapping data in found"):
        pc = mr.extract_observation(pointobs_epl_hm0)

    assert pc == None


@pytest.mark.skip(
    reason="validation not possible at the moment, allow item mapping for ModelResult and Observation and match on item name?"
)
def test_XArrayModelResultItem_extract_point_wrongitem(mr_ERA5_pp1d, pointobs_epl_hm0):
    mri = mr_ERA5_pp1d
    pc = mri.extract_observation(pointobs_epl_hm0)
    assert pc == None


def test_XArrayModelResultItem_extract_track(mr_ERA5_pp1d, trackobs_c2_hm0):
    mri = mr_ERA5_pp1d
    tc = mri.extract_observation(trackobs_c2_hm0)
    df = tc.data

    assert isinstance(tc, TrackComparer)
    assert tc.start.replace(microsecond=0) == datetime(2017, 10, 27, 12, 52, 52)
    assert tc.end.replace(microsecond=0) == datetime(2017, 10, 29, 12, 51, 28)
    assert tc.n_models == 1
    assert tc.n_points == 99
    assert tc.n_variables == 1
    assert len(df.dropna()) == 99


def test_xarray_connector(mr_ERA5_pp1d, pointobs_epl_hm0, trackobs_c2_hm0):
    con = fmskill.Connector([pointobs_epl_hm0, trackobs_c2_hm0], mr_ERA5_pp1d)
    assert len(con) == 2
    assert con.n_models == 1

    cc = con.extract()
    assert len(cc) == 2
