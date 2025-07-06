import hashlib
import time
from dotenv import load_dotenv
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests
import psycopg2

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

# Step 2: Create a PostgreSQL table to store event links if it doesn't exist
cur = conn.cursor()
with open("schema-urls.sql", "r") as f:
    cur.execute(f.read())
conn.commit()
print("Table 'schema_urls' created or already exists.")

# Step 3: Create a custom ID generator for URLs
def generate_url_id(url: str) -> str:
    return hashlib.sha256(url.encode('utf-8')).hexdigest()[:8]

# Step 4: Function to insert event links into the PostgreSQL table
def insert_event(url):
    id = generate_url_id(url)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO schema_urls (id, url)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, (id, url))
    conn.commit()

# Step 5: Custom Loader for Eventbrite.com for scraping event URLs from homepage
def load_eventbrite_events(url: str) -> list[str]:
    parsed = urlparse(url)
    if parsed.netloc not in ("www.eventbrite.com", "eventbrite.com"):
        return []
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

    soup = BeautifulSoup(resp.text, "lxml")

    # Find all links that match the Eventbrite event URL pattern ("https://www.eventbrite.com/e/rooftop-party-w-shingo-nakamura-at-hotel-via-tickets-1267566137439?aff=ebdssbdestsearch")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.match(r"https://www\.eventbrite\.com/e/.*", href):
            href = href.split("?")[0]
            insert_event(href)  # Insert the event link into the database
    
# Step 6: Scrape Eventbrite event links from the first 20 pages of the "Paid Events in various Locations" category
# Note: Adjust the range in the loop to scrape more pages if needed
# 
locations = ['ga--atlanta','fl--miami','ca--los-angeles']
for location in locations:
    print(f"Starting to scrape events for location: {location}")
    for i in range(1, 21):  # Scrape the first 20 pages
        load_eventbrite_events(f"https://www.eventbrite.com/d/{location}/paid--events/?page={i}&cur=USD")
        print(f"Page {i} of 20 scraped")
        time.sleep(5)  # Sleep for 5 seconds to avoid overwhelming the server
    print(f"Finished scraping events for location: {location}")

cur.execute("SELECT COUNT(*) FROM schema_urls;")
count = cur.fetchone()[0]
print(f"Total unique event links stored in the database: {count}")

# Step 7: Close the PostgreSQL connection
cur.close()
conn.close()