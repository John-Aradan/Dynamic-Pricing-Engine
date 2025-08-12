import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

# load environment variables from .env file
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

# Step 2: Fetch all rows from schema_events table
cur.execute("SELECT * FROM schema_events;")
rows = cur.fetchall()

# Step 3: Convert rows to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cur.description])

# Step 4: Save DataFrame to CSV
df.to_csv("Data/events_data.csv", index=False)