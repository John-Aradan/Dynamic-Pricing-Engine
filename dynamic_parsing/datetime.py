from dateparser.search import search_dates
from dateparser.date import DateDataParser
import pytz
import re

time_zones = ['PST', 'PDT', 'MST', 'MDT', 'CST', 'CDT', 'EST', 'EDT']
months = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

def is_multi_day(text: str) -> bool:
    left, right = [part.strip() for part in text.split("-", 1)]
    for month in months:
        if month in right:
            return True
    return False

def clean_single_day_range(date):
    start, end = [part.strip() for part in date.split("-", 1)]

    start_parts = start.split()
    month_day = " ".join(start_parts[:2])

    match = re.search(r"am|pm",end.lower())
    meridian = match.group(0) if match else ""      # am or pm

    full_start = f"{start}{meridian}"
    full_end = f"{month_day} {end}"

    return full_start, full_end

def is_valid_datetime_result(start, end=None):
    try:
        start = start[0][1]
        end = end[0][1]
        if not (1900 <= start.year <= 2100):
            return False
        if end and start > end:
            return False
        return True
    except Exception:
        return False
def get_time_of_day(hour):
    if 5 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 17:
        return 'afternoon'
    elif 17 <= hour < 21:
        return 'evening'
    else:
        return 'night'

def build_dict(start, end, timing_type):

    dt_start = start[0][1]
    dt_end = end[0][1] if end else None

    utc_start = dt_start.astimezone(pytz.utc)
    utc_end = dt_end.astimezone(pytz.utc) if dt_end else None

    duration = int((utc_end - utc_start).total_seconds() / 60) if utc_end else None
    time_of_day = get_time_of_day(dt_start.hour)
    day_of_week = dt_start.weekday()

    return {
        "local_start": dt_start,
        "utc_start": utc_start,
        "local_end": dt_end,
        "utc_end": utc_end,
        "timing_type": timing_type,
        "duration": duration,
        "time_of_day": time_of_day,
        "day_of_week": day_of_week
    }


def parse_event_datetime(date):
    try:
        
        timing_type = "None"
        
        date = date.split(",")[-1].strip().replace(" ·","")
        tiz = date.split(" ")[-1]
        for tz in time_zones:
            date = date.replace(tz, "")

        start = None
        end = None

        # Has Range
        if "-" in date:
            # Multi-Day
            if is_multi_day(date):
                dates = [d.strip() for d in date.split("-")]
                start = search_dates(f"{dates[0]} {tiz}", settings={ 'RETURN_AS_TIMEZONE_AWARE': True})
                end = search_dates(f"{dates[1]} {tiz}", settings={ 'RETURN_AS_TIMEZONE_AWARE': True})
                timing_type = "Multi-Day"
            # Single-Day
            else:
                start , end = clean_single_day_range(date)
                start = search_dates(f"{start} {tiz}", settings={ 'RETURN_AS_TIMEZONE_AWARE': True})
                end = search_dates(f"{end} {tiz}", settings={ 'RETURN_AS_TIMEZONE_AWARE': True})
                timing_type = "Single-Day-Ranged"
        # No Range
        # Single-Day (No Range)
        else:
            start = search_dates(f"{date} {tiz}", settings={ 'RETURN_AS_TIMEZONE_AWARE': True})
            timing_type = "Single-Day-Instant"
        if is_valid_datetime_result(start, end):
            return build_dict(start,end,timing_type)
        else:
            return None
    
    except Exception:
        return None

if __name__ == "__main__":
    test_date = "Saturday, July 26 · 2:30 - 6pm PDT"
    datetime = parse_event_datetime(test_date)
    print(datetime.get("local_start"))