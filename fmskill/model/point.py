from pathlib import Path
from typing import Union, get_args
import mikeio
import pandas as pd

from fmskill import types, utils
from fmskill.model._base import ModelResultBase


class PointModelResult(ModelResultBase):
    """Construct a PointModelResult from a dfs0 file,
    mikeio.Dataset/DataArray or pandas.DataFrame/Series

    Parameters
    ----------
    data : types.UnstructuredType
        the input data or file path
    name : Optional[str], optional
        The name of the model result,
        by default None (will be set to file name or item name)
    x : float, optional
        first coordinate of point position, by default None
    y : float, optional
        second coordinate of point position, by default None
    item : Optional[Union[str, int]], optional
        If multiple items/arrays are present in the input an item
        must be given (as either an index or a string), by default None
    itemInfo : Optional[mikeio.ItemInfo], optional
        Optionally, a MIKE IO ItemInfo (MIKE EUM system) can be given
        to set or override the type and unit of the quantity, by default None
    quantity : Optional[str], optional
        A string to identify the quantity, by default None
    """

    def __init__(
        self,
        data: types.PointType,
        *,
        name: str = None,
        x: float = None,
        y: float = None,
        item: Union[str, int] = None,
        itemInfo: mikeio.ItemInfo = None,
        quantity: str = None,
    ) -> None:
        assert isinstance(
            data, get_args(types.PointType)
        ), "Could not construct PointModelResult from provided data"

        if isinstance(data, (str, Path)):
            assert Path(data).suffix == ".dfs0", "File must be a dfs0 file"
            name = name or Path(data).stem
            data = mikeio.read(data)  # now mikeio.Dataset
        elif isinstance(data, mikeio.Dfs0):
            data = data.read()  # now mikeio.Dataset

        # parse item and convert to dataframe
        if isinstance(data, mikeio.Dataset):
            item_names = [i.name for i in data.items]
            item, idx = utils.get_item_name_and_idx(item_names, item)
            itemInfo = itemInfo or data.items[idx]
            data = data[[item]].to_dataframe()
        elif isinstance(data, mikeio.DataArray):
            item = item or data.name
            itemInfo = itemInfo or data.item
            data = mikeio.Dataset({data.name: data}).to_dataframe()
        elif isinstance(data, pd.DataFrame):
            item_names = list(data.columns)
            item, idx = utils.get_item_name_and_idx(item_names, item)
            data = data[[item]]
        elif isinstance(data, pd.Series):
            data = pd.DataFrame(data)  # to_frame?
            item = item or data.columns[0]
        else:
            raise ValueError("Could not construct PointModelResult from provided data")

        name = name or item

        # basic processing
        data = data.dropna()
        if data.empty or len(data.columns) == 0:
            raise ValueError("No data.")
        data.index = utils.make_unique_index(data.index, offset_duplicates=0.001)

        super().__init__(
            data=data, name=name, item=item, itemInfo=itemInfo, quantity=quantity
        )
        self.x = x
        self.y = y