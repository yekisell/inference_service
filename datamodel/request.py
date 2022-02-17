from pydantic import BaseModel


class RossmannRequest(BaseModel):
    Id: int = 0
    Store: int = 1
    DayOfWeek: int = 1
    Date: str = '2015-08-01'
    Open: bool = 1
    Promo: bool = 0
    StateHoliday: str = '0'
    SchoolHoliday: bool = 0
