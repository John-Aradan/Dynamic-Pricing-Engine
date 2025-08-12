from dotenv import load_dotenv
import os
from openai import RateLimitError
import psycopg2
from extract_event_details import extract_event_details
import time
from datetime import datetime
from tqdm import tqdm
import time
from collections import deque

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

cur = conn.cursor()

# Uncomment and run the following code to reset the status of all URLs to 'Pending' and reset attempts to 0
# cur.execute("""
#     UPDATE schema_urls
#     SET status = 'Pending',
#         no_attempts = 0;
# """)
# conn.commit()
# print("✅ Reset all rows in schema_urls to Pending with 0 attempts.")

cur.execute("SELECT * FROM schema_urls WHERE status IN ('Pending', 'Failed') AND no_attempts = 1;")
rows = cur.fetchall()

print(len(rows), "rows found in schema_urls table.")

# Step 2: Create a PostgreSQL table to store events
with open("schema-events.sql", "r") as f:
    cur.execute(f.read())
conn.commit()
print("Table 'schema_events' created or already exists.")

# track time stamp of last 3 OpenAI API calls
last_api_calls = deque(maxlen=3)

# create a function to check wait if 3 API calls have been made in the last 60 seconds
def wait_for_api_call():
    if len(last_api_calls) < 3:
        return
    now = time.time()
    elapsed = now - last_api_calls[0]
    if elapsed < 60:
        wait_time = 60 - elapsed
        print(f"[RateLimit] Waiting {wait_time:.2f}s to respect OpenAI limit...")
        time.sleep(wait_time)
    last_api_calls.append(now)

for idx, row in enumerate(tqdm(rows, desc="Processing events"), start=0):
    id = row[0]
    url = row[1]
    attempts = row[3]

    try:
        wait_for_api_call()
        start_time = time.time()
        event = extract_event_details(id,url)
        end_time = time.time()
        print(f"Extracted event: {event['title']} in {end_time - start_time:.2f} seconds")

        # Insert event into the database
        data_start_time = time.time()
        keys = ', '.join(event.keys())
        values = ', '.join(['%s'] * len(event))
        insert_query = f"INSERT INTO schema_events ({keys}) VALUES ({values}) ON CONFLICT (id) DO NOTHING;"
        cur.execute(insert_query, tuple(event.values()))

        # Update the status in schema_urls
        cur.execute("""UPDATE schema_urls 
                    SET status = 'Success', no_attempts = no_attempts + 1, last_attempt = %s, reason = 'NA'
                    WHERE id = %s;
                    """, (datetime.now(), id))
        conn.commit()
        data_end_time = time.time()
        print(f"Inserted event: {event['title']} in {data_end_time - data_start_time:.2f} seconds")

    except RateLimitError as e:
        # Attempt to read the recommended wait time
        retry_after = getattr(e, 'retry_after', 60)
        print(f"[RateLimit] Error: {e}. Waiting for {retry_after} seconds before retrying...")
        time.sleep(retry_after)
        continue
    
    except Exception as e:

        print(f"[ERROR] Failed to extract event from {url}: {e}")
        
        new_status = 'Dropped' if attempts >= 6 else 'Failed'
        cur.execute("""UPDATE schema_urls 
                    SET status = %s, no_attempts = no_attempts + 1, last_attempt = %s, reason = %s
                    WHERE id = %s;
                    """, (new_status, datetime.now(), str(e), id))
        conn.commit()
        continue
