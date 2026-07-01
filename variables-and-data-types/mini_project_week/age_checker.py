from datetime import datetime
from zoneinfo import ZoneInfo
from datetime import datetime

day = datetime.now().day
month = datetime.now().month
month_name_1 = datetime.now().strftime("%B")
month_name = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
# Create a timezone-aware object for New York
ny_time = datetime.now(ZoneInfo("America/New_York"))
print("New York time:", ny_time)

birth_month = str(input("what is your birth month? "))
birth_year = int(input("what is your birth year? "))
birth_month_day = int(input("what day of the month is your birth day? "))
birth_month_1 = month_name.get(birth_month.lower())
birth_month_accurate = month_name.get(month_name_1.lower())

current_age_year = ny_time.year - birth_year
current_age_month = birth_month_1 - birth_month_accurate
current_age_day = day - birth_month_day
print(f"You are {current_age_year} years, {current_age_month} months, and {current_age_day} days old.")