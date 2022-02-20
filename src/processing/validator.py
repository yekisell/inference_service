from datetime import datetime
from typing import Union

from src.datamodel.request import RossmannRequest


def is_in_range(value: int, range_list: list[int], attribute_name: str) -> None:
    if not range_list[0] <= value <= range_list[1]:
        raise ValueError(
            f"{attribute_name} must be >={range_list[0]} and <={range_list[1]}"
        )


def is_in_list(value: Union[int, str], value_list: list, attribute_name: str) -> None:
    if value not in value_list:
        raise ValueError(f"{attribute_name} must be in list {value_list}")


def sample_validation(sample: RossmannRequest) -> tuple[bool, str]:
    try:
        datetime.strptime(sample.Date, "%Y-%m-%d")
    except ValueError:
        return False, "Invalid Date! Print date in format YYYY-MM-DD"
    try:
        is_in_range(sample.Store, [1, 1115], "Store")
        is_in_range(sample.DayOfWeek, [1, 7], "DayOfWeek")

        is_in_list(sample.Open, [0, 1], "Open")
        is_in_list(sample.Promo, [0, 1], "Promo")
        is_in_list(sample.SchoolHoliday, [0, 1], "SchoolHoliday")
        is_in_list(sample.StateHoliday, ["0", "a", "b", "c"], "StateHoliday")

        return True, ""
    except ValueError as error:
        return False, str(error)
