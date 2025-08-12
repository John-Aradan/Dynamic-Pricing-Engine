import os
import googlemaps
import requests
from dotenv import load_dotenv
import redis
import json
from pydantic import BaseModel
from pydantic import ValidationError
# from walkscore import WalkScoreAPI

# Step 0: Load enviornment variables and setup Redis
load_dotenv()
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
# print(redis_client.ping())  # Should output: True

# Step 1: Setup Google Maps Client
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

class Geocode(BaseModel):
    formatted_address: str
    zip: str
    lat: float
    lon: float
    neighborhood: str | None = None

# Def: Geocode Addresses
def geocode_address(addr):
    res = gmaps.geocode(addr)
    if not res:
        return None
    result = res[0]
    comp = result.get("address_components",[])
    def get_type(t):
        for c in comp:
            if t in c["types"]:
                return c["long_name"]
        return None
    
    return {
        "formatted_address": result.get("formatted_address"),
        "zip": get_type("postal_code"),
        "lat": result["geometry"]["location"]["lat"],
        "lon": result["geometry"]["location"]["lng"],
        "neighborhood": get_type("neighborhood")
    }

poi_types = {
    "food_bev": ["restaurant", "cafe", "bar","bakery"],
    "access": ["gas_station", "parking", "transit_station"],
    "lodging": ["hotel", "rv_park", "lodge"]
}

class POIFeatures(BaseModel):
    food_bev_density: int
    food_bev_popularity_score: float
    access_density: int
    access_popularity_score: float
    lodging_density: int
    lodging_popularity_score: float

# Def: POI Density & Popularity
def poi_features_by_zip(zip_code, radius=1000):

     # Step 1: Geocode ZIP → lat/lon
    geocode_result = gmaps.geocode(zip_code)
    if not geocode_result:
        return {}
    location = geocode_result[0]['geometry']['location']
    lat, lon = location['lat'], location['lng']

    # Step 2: Loop through poi_types to retreive count and popularity
    features = {}
    for label, types in poi_types.items():
        count = 0
        popularity = 0
        total_reviews = 0
        for t in types:
            try:
                res = gmaps.places_nearby(location=(lat, lon), radius=radius, type=t)
                results = res.get("results", [])
                count += len(results)
                # Making the Places Details API call
                for r in results[:5]:
                    pid = r["place_id"]
                    det = gmaps.place(place_id=pid, fields=["rating", "user_ratings_total"])    # rating (e.g., 4.3 out of 5) total (e.g., 150 reviews)
                    pd = det.get("result", {})
                    popularity += pd.get("rating", 0) * pd.get("user_ratings_total", 0)
                    total_reviews += pd.get("user_ratings_total", 0)
            except Exception as exp:
                print(f"Error fetching type '{t}' for ZIP {zip_code}: {exp}")
                continue
        popularity = popularity / total_reviews if total_reviews else 0
        features[f"{label}_density"] = count
        features[f"{label}_popularity_score"] = popularity
    
    return features

# Def: A Redis wrapper that checks if the information exists in Cache already before making an API request
def poi_features_by_zip_cached(zip_code, radius=1000, ttl=2592000): # ttl: save cache for 30 days
    key = f"poi_zip:{zip_code}"
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    features = poi_features_by_zip(zip_code, radius)
    redis_client.set(key, json.dumps(features), ex=ttl)
    return features

ACS_VARIABLES = {
    "average_income_zip": "B19013_001E",  # Median household income
    "total_population": "B01003_001E",    # Total population (for density)
    "median_age": "B01002_001E",          # Median age
}

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")

class Census(BaseModel):
    average_income_zip: int
    population_total: int
    median_age: float

# Def: Connect to US Census Dataset to collect Demographic Information
def fetch_census_features(zip_code):
    base_url = "https://api.census.gov/data/2022/acs/acs5"
    vars_string = ",".join(ACS_VARIABLES.values())
    params = {
        "get": vars_string,
        "for": f"zip code tabulation area:{zip_code}",
        "key": CENSUS_API_KEY
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        headers = data[0]
        values = data[1]

        result = dict(zip(headers, values))

        return {
            "average_income_zip": int(result[ACS_VARIABLES["average_income_zip"]]),
            "population_total": int(result[ACS_VARIABLES["total_population"]]),
            "median_age": float(result[ACS_VARIABLES["median_age"]])
        }

    except Exception as e:
        print(f"Error fetching census data for ZIP {zip_code}: {e}")
        return {}

"""Waiting to hear back"""
# WALKSCORE_API_KEY = os.getenv("WALKSCORE_API_KEY")
# # Def: Fetch Walk, Transit Scores for the provided lan, lon data

def geocode_address_checked(addr):
    raw = geocode_address(addr)
    try:
        geocode = Geocode(**raw)
    except ValidationError as e:
        print("Validation failed:", e.errors())
        return None
    return geocode.model_dump()

def poi_features_by_zip_cached_checked(zip_code):
    raw = poi_features_by_zip_cached(zip_code)
    try:
        poi = POIFeatures(**raw)
    except ValidationError as e:
        print("Validation failed:", e.errors())
        return None
    return poi.model_dump()

def fetch_census_features_checked(zip_code):
    raw = fetch_census_features(zip_code)
    try:
        census = Census(**raw)
    except ValidationError as e:
        print("Validation failed:", e.errors())
        return None
    return census.model_dump()

def parse_event_location(location):
    geocode_info = geocode_address_checked(location)
    poi_features = poi_features_by_zip_cached_checked(geocode_info.get("zip"))
    census_demo_data = fetch_census_features_checked(geocode_info.get("zip"))
    return geocode_info, poi_features, census_demo_data

if __name__ == "__main__":
    location = "11015 Folsom1015 Folsom St San Francisco, CA 94103Get directions"
    geocode, poi, census = parse_event_location(location)
    for g in geocode.keys():
        print(f"{g} : {geocode.get(g)}")
    for p in poi.keys():
        print(f"{p} : {poi.get(p)}")
    for k in census.keys():
        print(f"{k} : {census.get(k)}")