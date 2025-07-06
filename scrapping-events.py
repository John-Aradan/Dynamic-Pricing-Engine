import hashlib
import time
from dotenv import load_dotenv
import re
import os
from bs4 import BeautifulSoup
import requests
import psycopg2
from urllib.parse import urlparse

# Step 0: Load environment variables from .env file
load_dotenv()

# Step 1: Set up PostgreSQL connection
conn = psycopg2.connect(
    host = os.getenv("POSTGRESQL_HOST"),
    port = 5432,
    database = "postgres",
    user = "postgres",
    password = os.getenv("POSTGRESQL_PASSWORD")
)

# Step 2: Create a PostgreSQL table to store events
cur = conn.cursor()
with open("schema-events.sql", "r") as f:
    cur.execute(f.read())
conn.commit()
print("Table 'schema_events' created or already exists.")

# Step 2.1: Set up headers for web scraping
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

# Step 3: Create a custom ID generator for events
def generate_event_id(title):
    return hashlib.sha256(title.encode('utf-8')).hexdigest()[:8]

# Step 4: Function to insert event details into the PostgreSQL table
def insert_event(event):
    id = generate_event_id(event['title'])
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO schema_events (id, title, day_of_week, time_of_day, location_city, venue_zone_type)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, (id, event['title'], event['day_of_week'], event['time_of_day'], event['location_city'], event['venue_zone_type']))
    conn.commit()

# Step 5: Extract event details from the url for Eventbrite.com
def extract_event_details_eventbrite(url: str) -> dict:

    parsed = urlparse(url)
    if parsed.netloc not in ("www.eventbrite.com", "eventbrite.com"):
        return {}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    event = {}
    title = soup.find("h1", class_=re.compile(r"event-title css-.*"))
    if not title:
        return {}
    event['title'] = title.get_text(strip=True())
    
    date = soup.find("div", attrs={"data-testid": "display-date-container"})
    if not date:
        return {}
    event['date'] = date.get_text(strip=True())
    

    location = soup.find("div", class_="location-info__address") # Find the address div
    if location:
        address = " ".join(list(location.stripped_strings)[1:2]) # Get the second string in the stripped strings
    print(address)
    cost = soup.find("div", class_="conversion-bar__body")
    if cost:
        print(cost.get_text(strip=True()))
    event_description = soup.find("div", class_="eds-l-mar-bot-12 structured-content").get_text(separator="\n", strip=True)
    print(event_description)