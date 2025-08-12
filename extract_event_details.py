import bs4
import requests
import re
from dynamic_parsing.datetime import parse_event_datetime
from dynamic_parsing.location import parse_event_location
from dynamic_parsing.price import parse_event_price
from dynamic_parsing.description import parse_event_description
import time

### This module extracts event details from an Eventbrite event page with a given URL.

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

def extract_event_details(id, url):
    
    resp = requests.get(url, headers=headers)
    if resp.status_code == 404:
        print(f"[ERROR] 404 Not Found {url}")
        raise ValueError("Event not found (404)")
    
    resp.raise_for_status()

    soup = bs4.BeautifulSoup(resp.text, "lxml")

    title_tag = soup.find("h1", class_=re.compile(r"event-title css-.*"))
    if not title_tag:
        raise ValueError("Event title not found")
    title = title_tag.get_text(strip=True)

    
    date_time = soup.find("div", attrs={"data-testid": "display-date-container"})
    if not date_time:
        raise ValueError("Event date and time not found")
    # print(date_time.get_text(strip=True))
    datetime = parse_event_datetime(date_time.get_text(strip=True))

    location = soup.find("div", class_="location-info__address")
    if not location:
        raise ValueError("Event location not found")
    geocode, poi, census = parse_event_location(location)

    cost = soup.find("div", class_="conversion-bar__body")
    if not cost:
        raise ValueError("Event cost not found")
    cost = parse_event_price(cost.get_text(strip=True))
    if cost is None or cost == 0 or cost == "":
        raise ValueError("Event cost is invalid or 0")

    event_description = soup.find("div", class_="eds-l-mar-bot-12 structured-content")
    if not event_description:
        raise ValueError("Event description not found")
    desc = parse_event_description(event_description.get_text(separator="\n", strip=True))

    return {
        "id": id,
        "title": title,
        "url": url,
        "local_start": datetime['local_start'],
        "utc_start": datetime['utc_start'],
        "local_end": datetime['local_end'],
        "utc_end": datetime['utc_end'],
        "timing_type": datetime['timing_type'],
        "duration": datetime['duration'],
        "time_of_day": datetime['time_of_day'],
        "day_of_week": datetime['day_of_week'],
        "event_season": datetime['event_season'],
        "formatted_address": geocode['formatted_address'],
        "zip": geocode['zip'],
        "lat": geocode['lat'],
        "lon": geocode['lon'],
        "neighborhood": geocode['neighborhood'],
        "food_bev_density": poi['food_bev_density'],
        "food_bev_pop_score": poi['food_bev_popularity_score'],
        "access_density": poi['access_density'],
        "access_pop_score": poi['access_popularity_score'],
        "lodging_density": poi['lodging_density'],
        "lodging_pop_score": poi['lodging_popularity_score'],
        "average_income_zip": census['average_income_zip'],
        "population_zip": census['population_total'],
        "median_age_zip": census['median_age'],
        "event_type": desc['Event_Type'],
        "target_audience": desc['Target_Audience'],
        "event_mood_energy": desc['Event_mood_Energy'],
        "freebies_included": desc['Freebies_Included'],
        "uniqueness": desc['Uniqueness'],
        "price": cost
    }

if __name__ == "__main__":
    url = "https://www.eventbrite.com/e/gay-mens-sangha-tickets-1335554632859"
    id = "devxe67r"
    try:
        # check how long it takes to extract event details
        start_time = time.time()
        event = extract_event_details(id, url)
        end_time = time.time()
        print(f"Time taken to extract event details: {end_time - start_time:.2f} seconds")
        for key, value in event.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"Error extracting event details: {e}")