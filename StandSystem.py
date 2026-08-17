from flask import Flask, request, jsonify
import os
import random
import requests
from supabase import create_client, Client

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_SECRET = os.getenv("API_SECRET")

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

MODIFIERS = [
    {
        "name": "Normal",
        "chance": 60.0,
        "rarity_bonus": 0
    },

    {
        "name": "Shiny",
        "chance": 20,
        "rarity_bonus": 1
    },

    {
        "name": "Rainbow",
        "chance": 15,
        "rarity_bonus": 3
    },

    {
        "name": "Ethereal",
        "chance": 5,
        "rarity_bonus": 5
    }
]

RARITY_LEVELS = {
    "Common": 0,
    "Uncommon": 1,
    "Rare": 2,
    "Epic": 3,
    "Legendary": 4,
    "???": 5
}

RARITY_NAMES = [
    "Common",
    "Uncommon",
    "Rare",
    "Epic",
    "Legendary",
    "???"
]

        #Common Stands
STANDS = [
    {
        "name": "Hermit Purple",
        "rarity": "COMMON",
        "weight": 100
    },
    {
        "name": "Survivor",
        "rarity": "COMMON",
        "weight": 100
    },
    {
        "name": "Cheap Trick",
        "rarity": "COMMON",
        "weight": 90
    },
    {
        "name": "Tohth",
        "rarity": "COMMON",
        "weight": 90
    },
        #Uncommon Stands
    {
        "name": "The Fool",
        "rarity": "UNCOMMON",
        "weight": 60,
    },

    {
        "name": "Hierophant Green",
        "rarity": "UNCOMMON",
        "weight": 60
    },

    {
        "name": "Aerosmith",
        "rarity": "UNCOMMON",
        "weight": 55
    },

    {
        "name": "Sex Pistols",
        "rarity": "UNCOMMON",
        "weight": 55
    },
    # Rare Stands
    {
        "name": "Silver Chariot",
        "rarity": "RARE",
        "weight": 30
    },

    {
        "name": "Magician's Red",
        "rarity": "RARE",
        "weight": 30
    },

    {
        "name": "Sticky Fingers",
        "rarity": "RARE",
        "weight": 25
    },

    {
        "name": "The Hand",
        "rarity": "RARE",
        "weight": 25
    },

    {
        "name": "Heaven's Door",
        "rarity": "RARE",
        "weight": 20
    },
    # Epic Stands
    {
        "name": "Crazy Diamond",
        "rarity": "EPIC",
        "weight": 12
    },

    {
        "name": "Killer Queen",
        "rarity": "EPIC",
        "weight": 12
    },

    {
        "name": "King Crimson",
        "rarity": "EPIC",
        "weight": 10
    },

    {
        "name": "D4C",
        "rarity": "EPIC",
        "weight": 10
    },

    {
        "name": "Stone Free",
        "rarity": "EPIC",
        "weight": 10
    },
    # Legendary Stands
    {
        "name": "Star Platinum",
        "rarity": "LEGENDARY",
        "weight": 5
    },

    {
        "name": "The World",
        "rarity": "LEGENDARY",
        "weight": 5,
        "sound": "the_world"
    },

    {
        "name": "Gold Experience",
        "rarity": "LEGENDARY",
        "weight": 4
    },

    {
        "name": "Made in Heaven",
        "rarity": "LEGENDARY",
        "weight": 3
    },

    {
        "name": "C-Moon",
        "rarity": "LEGENDARY",
        "weight": 3
    },

    {
        "name": "Tusk ACT 4",
        "rarity": "LEGENDARY",
        "weight": 3
    },
    # ??? Stands
    {
        "name": "Gold Experience Requiem",
        "rarity": "???",
        "weight": 1
    },

    {
        "name": "Wonder of U",
        "rarity": "???",
        "weight": 1
    },

]

def get_twitch_access_token():

    response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
    )

    if response.status_code != 200:
        print("Twitch token error:")
        print(response.text)

        return None

    return response.json()["access_token"]


def get_twitch_user_id(username):

    if not username:
        return None

    username = username.strip().lower()

    print(f"Looking up Twitch user: {username}")

    access_token = get_twitch_access_token()

    if not access_token:
        return None

    response = requests.get(
        "https://api.twitch.tv/helix/users",
        params={
            "login": username
        },
        headers={
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }
    )

    print("Twitch lookup status:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        return None

    users = response.json().get("data", [])

    if not users:
        return None

    return users[0]["id"]


def get_twitch_username_from_id(twitch_id):

    if not twitch_id:
        return None

    access_token = get_twitch_access_token()

    if not access_token:
        return None

    response = requests.get(
        "https://api.twitch.tv/helix/users",
        params={
            "id": twitch_id
        },
        headers={
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }
    )

    if response.status_code != 200:
        print("Twitch username lookup failed:")
        print(response.text)

        return None

    users = response.json().get("data", [])

    if not users:
        return None

    return users[0]["display_name"]


def roll_modifier():

    roll = random.random()

    current = 0

    for modifier in MODIFIERS:

        current += modifier["chance"]

        if roll <= current:

            return modifier

    return MODIFIERS[0]

def roll_stand():

    stand = random.choice(STANDS)

    modifier = roll_modifier()

    return {
        "stand": stand,
        "modifier": modifier,
    }

def get_user_stand(twitch_id):

    result = (
        supabase
        .table("stand_users")
        .select("*")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]

def set_user_stand(
    twitch_id,
    stand_name,
    modifier=None
):

    data = {
        "twitch_id": twitch_id,
        "stand": stand["name"],
        "modifier": modifier["name"] if modifier else "Normal"
    }

    result = (
        supabase
        .table("stand_users")
        .upsert(data)
        .execute()
    )

    return result.data

def roll_stand_for_user(twitch_id):

    result = roll_stand()

    set_user_stand(
        twitch_id,
        result["stand"],
        result["modifier"]
    )

    return result

def reroll_stand(twitch_id):

    existing = get_user_stand(twitch_id)

    if not existing:
        return None

    result = roll_stand()

    set_user_stand(
        twitch_id,
        result["stand"],
        result["modifier"]
    )

    return