from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from pydantic import BaseModel
from pydantic import ValidationError


# Step 0: Setup Env variables and OpenAI API
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

system_prompt = f"""
Generate a JSON file containing these exact features for the description I provide you:
1. Event_Type: One of the following (The main category of the event. It should summarize the primary purpose or format of the event)
The options only includes:
Business
Food & Drink
Health
Music
Auto, Boat & Air
Charity & Causes
Community
Family & Education
Fashion
Film & Media
Hobbies
Home & Lifestyle
Performing & Visual Arts
Government
Spirituality
School Activities
Science & Tech
Holidays
Sports & Fitness
Travel & Outdoor

2. Target_Audience : The specific group(s) of people the event is aimed at, based on age, interests, profession, or community.
The options only includes:
Families with Children
Teens / High School Students
College Students
Young Adults (18 to 30)
Adults / Professionals (25 to 45)
Seniors / Older Adults (50+)

3. Event_mood_Energy : The emotional tone, mood, or energy level of the event, as implied by the description. Think of the vibe of the experience.
The options only includes:
Formal
Relaxed
High-Energy
Educational
Spiritual
Romantic
Adventurous
Professional 

4. Freebies_Included: Indicate whether the event description mentions any items or services provided for free to attendees — including food, drinks, merchandise, gear, swag, etc.
The options only includes:
"Yes" if the description explicitly mentions free items (e.g., "includes complimentary snacks" or "free tote bag").
"No" if nothing free is mentioned or implied.

5. Uniqueness: Is there a uniqueness or exclusivity implied in the text? Is it a limited time event? Is it implied in text that this event is a one time thing that may not repeat again?
The options only includes:
"Yes" if any of the cases above is satisfied
"No" if none of them are satisfied

IMP: If any of the information is missing for values 1 to 3, please assign "None" as value in JSON

You must give the output in a JSON form with absolutely no additional text. Use this exact format:
{{
  "Event_Type": "...",
  "Target_Audience": "...",
  "Event_mood_Energy": "...",
  "Freebies_Included": "..."
  "Uniqueness": "..."
}}
"""

def create_user_prompt(desc):

    return f"""
    Gererate JSON in the following format with no additional text before or after. 

    format:
    {{
    "Event_Type": "...",
    "Target_Audience": "...",
    "Event_mood_Energy": "...",
    "Freebies_Included": "..."
    "Uniqueness": "..."
    }}

    Event description:
    {desc}
    """

# Def: Define a pydantic model (schema) used to verify required features returned and of the right datatype
class EventFeatures(BaseModel):
    Event_Type: str
    Target_Audience: str
    Event_mood_Energy: str
    Freebies_Included: str
    Uniqueness: str

def parse_description(desc):

    user_prompt = create_user_prompt(desc)

    tools = [{
        "type": "function",
        "name": "extract_event_features",
        "description": "Extract event value-based features for pricing from event description",
        "parameters": {
            "type": "object",
            "properties": {
                "Event_Type": {"type": "string"},
                "Target_Audience": {"type": "string"},
                "Event_mood_Energy": {"type": "string"},
                "Freebies_Included": {"type": "string"},
                "Uniqueness": {"type": "string"}
            },
            "required": [
                "Event_Type",
                "Target_Audience",
                "Event_mood_Energy",
                "Freebies_Included",
                "Uniqueness"
            ],
            "additionalProperties": False
        }
    }]

    # response = client.chat.completions.create(  ~> messages => input
    response = client.responses.create(
        model="gpt-3.5-turbo",
        temperature=0.3,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        tools=tools
    )

    call = response.output[0].arguments
    result = json.loads(call)
    return result

def parse_event_description(desc: str):
    raw = parse_description(desc)
    try:
        event = EventFeatures(**raw)
    except ValidationError as e:
        print("Validation failed:", e.errors())
    return event.model_dump()

if __name__ == "__main__":

    desc = """
    About this event
    Friday July 18th, 2025
    Rinse, SQUISH, Fluxions, DJ Dials & 1015 Folsom Present:
    SHADES
    Alix Perez (Belgium/UK) and Eprom (USA) are SHADES
    w/ Neffa-T, Jossy Mitsu, Breaka
    Perez found his rise to fame in drum n bass, releasing on Shogun Audio, Exit Recordings amongst many other labels and collaborating with the foremost names in dance and electronic music such as Noisia, Foreign Beggars, dBridge, and many more.
    Eprom gained his well-deserved success through his innovative take on bass music, a unique sound that has the likes of Gaslamp Killer, Kutmah, D-Styles singing his praises and supporting his music.
    SHADES exemplifies slanted grooves, a deep pocket and hard yet graceful composition. The debut self-titled EP (released on Alpha Pup) is a truly unique body of work.
    Aware of each other’s music for some time before meeting, Perez and Eprom first crossed paths at the 2013/2014 Northern Bass festival in New Zealand. The following summer they met again at the Red Bull Studios LA producing the Foreign Beggars’ Modus EP. This initial studio session led to further collaborations and SHADES was born.
    XLR8R have rightly said “music that’s not only a legitimate full-frontal assault in the same vein as tunes from that golden era of gluttonous bass and synths, but that embraces that ethos while giving it a more polished feel”.    
    21+
    """

    result = parse_event_description(desc)
    for k in result.keys():
        print(f"{k}: {result.get(k)}")
