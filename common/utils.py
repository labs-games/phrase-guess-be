import datetime
from typing import Callable, Optional, TypeVar

import pytz

from .configs import PARAMS_DATE_FORMAT, SINGAPORE_TIMEZONE

# pylint: disable=invalid-name
T = TypeVar("T")
U = TypeVar("U")


def split_int(string: str, delimiter: str = ",") -> list[int]:
    return list(int(elem.strip()) for elem in string.split(delimiter) if elem.strip())


def split_str(string: str, delimiter: str = ",") -> list[str]:
    return list(elem.strip() for elem in string.split(delimiter) if elem.strip())


def to_dt(string: str, date_format: str = PARAMS_DATE_FORMAT) -> datetime.datetime:
    return utc_localize(datetime.datetime.strptime(string, date_format))


def to_end_of_day(dt: datetime.datetime) -> datetime.datetime:
    return utc_localize(datetime.datetime.combine(dt, datetime.time.max))


def get_dates_in_between(start_date: datetime.date, end_date: datetime.date) -> list[datetime.date]:
    current_date: datetime.date = start_date
    # start_date and end_date is inclusive
    dates_in_between: list[datetime.date] = []
    while current_date <= end_date:
        dates_in_between.append(current_date)
        current_date += datetime.timedelta(days=1)
    return dates_in_between


def unwrap_or_default(elem: Optional[T], default: T) -> T:
    return elem if elem is not None else default


def apply_or_ignore(elem: Optional[T], f: Callable[[T], U]) -> Optional[U]:
    if elem is None:
        return None
    return f(elem)


def sgt_localize(dt: datetime.datetime) -> datetime.datetime:
    return pytz.timezone(SINGAPORE_TIMEZONE).localize(dt)


def utc_localize(dt: datetime.datetime) -> datetime.datetime:
    return pytz.utc.localize(dt)


def sgt_now() -> datetime.datetime:
    return sgt_localize(datetime.datetime.now())


def utc_now() -> datetime.datetime:
    return utc_localize(datetime.datetime.now())


def utc_to_sgt(dt: datetime.datetime) -> datetime.datetime:
    return dt.astimezone(pytz.timezone(SINGAPORE_TIMEZONE))


def parse_z_isoformat_dt(dt_str: str) -> datetime.datetime:
    z_removed_isoformat: str = dt_str.replace("Z", "")

    has_decimal: bool = "." in z_removed_isoformat
    if has_decimal:
        # datetime.datetime.fromisoformat needs at most 6 digits for seconds decimal
        allowed_decimal_digits: int = 6
        decimal_digits: int = len(z_removed_isoformat.split(".")[-1])
        if decimal_digits > allowed_decimal_digits:
            z_removed_isoformat = z_removed_isoformat[: -(decimal_digits - allowed_decimal_digits)]

    naive_dt: datetime.datetime = datetime.datetime.fromisoformat(z_removed_isoformat)
    utc_tz = pytz.utc
    return utc_tz.localize(dt=naive_dt)
