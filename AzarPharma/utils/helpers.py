# utils/helpers.py

from persiantools.jdatetime import JalaliDate

def gregorian_to_jalali(date_obj):
    """
    تاریخ Gregorian به Jalali (شمسی) تبدیل می‌کند.
    :param date_obj: datetime.date یا datetime.datetime
    :return: str
    """
    j = JalaliDate.to_jalali(date_obj.year, date_obj.month, date_obj.day)
    return f"{j.year}/{j.month:02d}/{j.day:02d}"

def jalali_to_gregorian(date_str):
    """
    تاریخ شمسی (رشته ای) به Gregorian (میلادی) تبدیل می‌کند.
    :param date_str: str به فرمت 'YYYY/MM/DD'
    :return: datetime.date
    """
    y, m, d = [int(x) for x in date_str.strip().split('/')]
    return JalaliDate(y, m, d).to_gregorian()

def format_currency(val: int) -> str:
    """
    تبدیل عدد به رشته با جداکننده سه‌رقمی و پسوند ریال
    """
    return f"{val:,} ریال"

def national_code_is_valid(nc: str) -> bool:
    """
    چک می‌کند که یک کد ملی ایران معتبر است یا نه.
    """
    if len(nc) != 10 or not nc.isdigit():
        return False
    check = int(nc[9])
    s = sum([int(nc[x]) * (10 - x) for x in range(9)]) % 11
    return (s < 2 and check == s) or (s >= 2 and check == 11 - check)