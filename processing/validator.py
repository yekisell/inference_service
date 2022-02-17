from datetime import datetime

from datamodel.request import RossmannRequest


def sample_validation(sample: RossmannRequest) -> tuple[bool, str]:
    try:
        datetime.strptime(sample.Date, '%Y-%m-%d')
    except ValueError:
        return False, "Invalid Date! Print date in format YYYY-MM-DD"
    try:
        if sample.Store < 1 or sample.Store > 1115:
            raise ValueError('Store must be >=1 and <=1115')
        if sample.DayOfWeek < 1 or sample.DayOfWeek > 7:
            raise ValueError('DayOfWeek must be >=1 and <=7')
        if sample.Open not in [0, 1]:
            raise ValueError('Open must be either 0 or 1')
        if sample.Promo not in [0, 1]:
            raise ValueError('Promo must be either 0 or 1')
        if sample.SchoolHoliday not in [0, 1]:
            raise ValueError('SchoolHoliday must be either 0 or 1')
        if sample.StateHoliday not in ['0', 'a', 'b', 'c']:
            raise ValueError("StateHoliday must be in ['0', 'a', 'b', 'c']")
        return True, ""
    except ValueError as error:
        return False, str(error)
