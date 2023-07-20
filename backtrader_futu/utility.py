from functools import lru_cache
import pickle
import sys
import commentjson
import orjson
import pandas as pd
from pathlib import Path
import datetime as dt
from typing import Callable, List, Dict, Optional, Type, Tuple
from datetime import datetime
from .object import ContractData

if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo, available_timezones  # noqa
else:
    from backports.zoneinfo import ZoneInfo, available_timezones  # noqa

CHINA_TZ = ZoneInfo("Asia/Shanghai")


def _get_trader_dir(temp_name: str) -> Tuple[Path, Path]:
    """
    Get path where trader is running in.
    """
    cwd: Path = Path.cwd()
    temp_path: Path = cwd.joinpath(temp_name)

    # If .vntrader folder exists in current working directory,
    # then use it as trader running path.
    if temp_path.exists():
        return cwd, temp_path

    # Otherwise use home path of system.
    home_path: Path = Path.home()
    temp_path: Path = home_path.joinpath(temp_name)

    # Create .vntrader folder under home path if not exist.
    if not temp_path.exists():
        temp_path.mkdir()

    return home_path, temp_path


TRADER_DIR, TEMP_DIR = _get_trader_dir(".trader")
sys.path.append(str(TRADER_DIR))


def get_file_path(filename: str) -> Path:
    """
    Get path for temp file with filename.
    """
    return TEMP_DIR.joinpath(filename)


def get_folder_path(folder_name: str) -> Path:
    """
    Get path for temp folder with folder name.
    """
    folder_path: Path = TEMP_DIR.joinpath(folder_name)
    if not folder_path.exists():
        folder_path.mkdir()
    return folder_path


def get_icon_path(filepath: str, ico_name: str) -> str:
    """
    Get path for icon file with ico name.
    """
    ui_path: Path = Path(filepath).parent
    icon_path: Path = ui_path.joinpath("ico", ico_name)
    return str(icon_path)


def load_json(filename: str, use_comments=False) -> dict:
    """
    Load data from json file in temp path.
    """
    filepath: Path = get_file_path(filename)

    if filepath.exists():
        with open(filepath, mode="r", encoding="UTF-8") as f:
            if use_comments:
                data: dict = commentjson.load(f)
            else:
                c = f.read()
                if len(c) > 0:
                    data: dict = orjson.loads(c)
                else:
                    data = {}
        return data
    else:
        # save_json(filename, {})
        return {}


def save_json(filename: str, data: dict) -> None:
    """
    Save data into json file in temp path.
    """
    filepath: Path = get_file_path(filename)
    with open(filepath, mode="wb") as f:
        s = orjson.dumps(
            data,
            option=orjson.OPT_APPEND_NEWLINE
            | orjson.OPT_INDENT_2
            | orjson.OPT_OMIT_MICROSECONDS
            | orjson.OPT_SERIALIZE_NUMPY,
        )
        f.write(s)


def generate_datetime(s: str) -> datetime:
    """生成时间戳"""
    if "." in s:
        dt: datetime = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
    else:
        dt: datetime = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

    dt: datetime = dt.replace(tzinfo=CHINA_TZ)
    return dt


def generate_datetime_from_ts(ts: pd.Timestamp) -> datetime:
    dts = ts.strftime("%Y-%m-%d %H:%M:%S")
    dt = generate_datetime(dts)
    return dt


@lru_cache(maxsize=999)
def load_contracts_cache(cache_data_path_: str, dt: dt.date) -> Dict[str, ContractData]:
    key = _get_pickle_contracts_key(dt)

    cache_data_path = _get_cache_path(cache_data_path_)

    path = cache_data_path.joinpath(key)
    if not path.exists():
        return None, key

    with open(str(path), "rb") as f:
        data = pickle.load(f)
        return data, key

    return None, key


def _get_pickle_contracts_key(dt: dt.date):
    key = "_".join(["backtrader_futu", "contracts", dt.strftime("%Y%m%d")])

    return key


def save_contracts_cache(data: Dict[str, ContractData], cache_data_path_: str, dt: dt.date) -> None:
    key = _get_pickle_contracts_key(dt)

    cache_data_path = _get_cache_path(cache_data_path_)

    if not cache_data_path.exists():
        cache_data_path.mkdir(parents=True)

    path = cache_data_path.joinpath(key)

    with open(str(path), "wb") as f:
        pickle.dump(data, f)


def _get_cache_path(cache_data_path_):
    if not cache_data_path_:
        cache_data_path = get_folder_path("contracts_cache")
    else:
        cache_data_path: Path = Path(cache_data_path_)

    return cache_data_path
