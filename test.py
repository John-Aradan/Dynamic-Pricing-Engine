import bs4
import requests
import re
from dynamic_parsing.datetime import parse_event_datetime

url = "https://www.eventbrite.com/e/4-day-pmp-workflow-training-in-san-francisco-ca-tickets-1002281219107"

headers = {
        "User-Agent": (                                     # This is a common user agent string for web scraping
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",    # Accept language header to specify English
        "Accept-Encoding": "gzip, deflate, br", # Accept encoding header to handle compressed responses
        "Referer": "https://www.google.com/"    # Referer header to indicate the source of the request
    }

resp = requests.get(url, headers=headers)
resp.raise_for_status()

soup = bs4.BeautifulSoup(resp.text, "lxml")

# use regex to find the title with a class that starts with "event-title css-"
title = soup.find("h1", class_=re.compile(r"event-title css-.*")).get_text(strip=True)

date_time = soup.find("div", attrs={"data-testid": "display-date-container"}).get_text(strip=True)
print(date_time)

datetime = parse_event_datetime(date_time)

# location = soup.find("div", class_="location-info__address") # Find the address div
# if location:
#     address = " ".join(list(location.stripped_strings)[1:2]) # Get the second string in the stripped strings
# print(address)
# cost = soup.find("div", class_="conversion-bar__body")
# if cost:
#     print(cost.get_text(strip=True))

# event_description = soup.find("div", class_="eds-l-mar-bot-12 structured-content").get_text(separator="\n", strip=True)
# print(event_description)