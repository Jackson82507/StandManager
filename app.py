import os
import random
import requests

from pathlib import Path

from flask import Flask, request, jsonify
from supabase import create_client
from dotenv import load_dotenv

import asyncio
import json
import uuid
import websockets


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_SECRET = os.getenv("API_SECRET")

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

STREAMELEMENTS_CHANNEL_ID = os.getenv("STREAMELEMENTS_CHANNEL_ID")
STREAMELEMENTS_JWT = os.getenv("STREAMELEMENTS_JWT")

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
    "COMMON": 0,
    "UNCOMMON": 1,
    "RARE": 2,
    "EPIC": 3,
    "LEGENDARY": 4,
    "MYTHIC": 5
}

RARITY_NAMES = [
    "COMMON",
    "UNCOMMON",
    "RARE",
    "EPIC",
    "LEGENDARY",
    "MYTHIC"
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

async def streamelements_listener():

    uri = "wss://astro.streamelements.com"

    while True:

        try:

            async with websockets.connect(uri) as websocket:

                print("Connected to StreamElements WebSocket")

                async for raw_message in websocket:

                    message = json.loads(raw_message)

                    message_type = message.get("type")

                    # StreamElements is ready
                    if message_type == "welcome":

                        print("StreamElements WebSocket authenticated")

                        await websocket.send(json.dumps({
                            "type": "subscribe",
                            "nonce": str(uuid.uuid4()),
                            "data": {
                                "topic": "channel.loyalty.redemptions",
                                "room": STREAMELEMENTS_CHANNEL_ID,
                                "token": STREAMELEMENTS_JWT,
                                "token_type": "jwt"
                            }
                        }))

                    # Subscription response
                    elif message_type == "response":

                        print("StreamElements response:")
                        print(message)

                    # Actual event
                    elif message_type == "message":

                        if message.get("topic") != "channel.loyalty.redemptions":
                            continue

                        print("LOYALTY REDEMPTION:")
                        print(json.dumps(message, indent=2))

                        await handle_redemption(message)

        except Exception as e:

            print("StreamElements WebSocket error:", e)
            print("Reconnecting in 5 seconds...")

            await asyncio.sleep(5)

async def handle_redemption(message):

    data = message.get("data", {})

    print("Redemption data:")
    print(json.dumps(data, indent=2))


def get_twitch_username_from_id(twitch_id):

    # Get Twitch app access token
    token_response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
    )

    print("Token status:", token_response.status_code)

    if token_response.status_code != 200:
        print("Twitch token error:")
        print(token_response.text)
        return None

    # Extract the newly generated access token
    access_token = token_response.json()["access_token"]

    # Ask Twitch for the user by ID
    user_response = requests.get(
        "https://api.twitch.tv/helix/users",
        params={
            "id": twitch_id
        },
        headers={
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }
    )

    print("User lookup status:", user_response.status_code)
    print("User lookup response:", user_response.text)

    if user_response.status_code != 200:
        return None

    users = user_response.json().get("data", [])

    if not users:
        print(f"Twitch ID '{twitch_id}' was not found.")
        return None

    username = users[0]["display_name"]

    print(f"Found Twitch username: {username}")

    return username

def get_twitch_user_id(username):

    username = username.strip().lower()

    print(f"Looking up Twitch user: {username}")

    # Get Twitch app access token
    token_response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
    )

    print("Token status:", token_response.status_code)

    if token_response.status_code != 200:
        print("Twitch token error:")
        print(token_response.text)
        return None

    access_token = token_response.json()["access_token"]

    # Ask Twitch for the user
    user_response = requests.get(
        "https://api.twitch.tv/helix/users",
        params={
            "login": username
        },
        headers={
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }
    )

    print("User lookup status:", user_response.status_code)
    print("User lookup response:", user_response.text)

    if user_response.status_code != 200:
        return None

    users = user_response.json().get("data", [])

    if not users:
        print(f"Twitch user '{username}' was not found.")
        return None

    twitch_id = users[0]["id"]

    print(f"Found Twitch ID: {twitch_id}")

    return twitch_id

    #
    # RANDOM STAND
    #

def get_random_stand():

    stands = STANDS

    weights = [
        stand["weight"]
        for stand in stands
    ]

    selected = random.choices(
        stands,
        weights=weights,
        k=1
    )[0]

    return selected

@app.route("/")
def home():

    return "Stand Manager API is running!"

@app.route("/stand")
def get_stand():

    twitch_id = request.args.get("twitch_id")

    if not twitch_id:
        return "Missing Twitch ID", 400

    result = (
        supabase
        .table("stand_users")
        .select("stand_name, rarity")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    if result.data:

        stand_name = result.data[0]["stand_name"]
        rarity = result.data[0]["rarity"]

        return (
            f"🌀 Your Stand is {stand_name} "
            f"[{rarity}]!"
        )

    stand = get_random_stand()

    stand_name = stand["name"]
    rarity = stand["rarity"]

    # Save Stand
    supabase.table("stand_users").insert({
        "twitch_id": twitch_id,
        "stand_name": stand_name,
        "rarity": rarity
    }).execute()

    return (
        f"🌀 You have received "
        f"{stand_name} [{rarity}]!"
    )

def roll_stand():

    names = []
    weights = []

    for stand in STANDS:

        names.append(stand)
        weights.append(stand["weight"])

    return random.choices(
        names,
        weights=weights,
        k=1
    )[0]

def roll_modifier():

    modifiers = []
    weights = []

    for modifier in MODIFIERS:

        modifiers.append(modifier)
        weights.append(modifier["chance"])

    return random.choices(
        modifiers,
        weights=weights,
        k=1
    )[0]

def reroll_stand(twitch_id):

    stand = roll_stand()

    modifier = roll_modifier()

    # Save
    supabase.table("stand_users").update({

        "stand_name": stand["name"],
        "rarity": stand["rarity"],
        "modifier": modifier["name"],

    }).eq(
        "twitch_id",
        twitch_id
    ).execute()

    return {
        "stand": stand,
        "modifier": modifier,
    }
REROLL_COST = 500

@app.route("/reroll")
def reroll():

    twitch_id = request.args.get("twitch_id")
    username = request.args.get("username")
    points = request.args.get("points")
    secret = request.args.get("secret")

    # Check API secret
    if secret != API_SECRET:
        return "Unauthorized", 401

    if not twitch_id:
        return "Missing Twitch ID", 400

    if not username:
        return "Missing username", 400

    # Make sure the user has a Stand
    result = (
        supabase
        .table("stand_users")
        .select("*")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    if not result.data:
        return "❌ You don't have a Stand yet.", 400

    deduct_streamelements_points(username, 1000)

    # Roll the new Stand
    roll_result = reroll_stand(twitch_id)

    stand = roll_result["stand"]
    modifier = roll_result["modifier"]

    return (
        f"🌀 {username} rolled "
        f"{stand['name']} "
        f"[{modifier['name']}] "
    )

@app.route("/setstandcommand")
def set_stand_command():

    username = request.args.get("username")
    stand_name = request.args.get("stand")
    secret = request.args.get("secret")

    # Security
    if secret != API_SECRET:
        return "Unauthorized", 401

    if not username:
        return "Missing username", 400

    if not stand_name:
        return "Missing Stand name", 400

    # Convert underscores back into spaces
    stand_name = stand_name.replace("_", " ")

    # Find the Stand
    selected_stand = None

    for stand in STANDS:

        if stand["name"].lower() == stand_name.lower():
            selected_stand = stand
            break

    if selected_stand is None:
        return f"Stand '{stand_name}' was not found.", 404

    # Find Twitch user
    twitch_id = get_twitch_user_id(username)

    if twitch_id is None:
        return f"Twitch user '{username}' was not found.", 404

    # Check if user already exists
    result = (
        supabase
        .table("stand_users")
        .select("twitch_id")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    # Update existing user
    if result.data:
        supabase.table("stand_users").update({
            "stand_name": selected_stand["name"],
            "rarity": selected_stand["rarity"],
            "modifier": "Normal",
        }).eq(
            "twitch_id",
            twitch_id
        ).execute()
    # Create new user
    else:
        supabase.table("stand_users").update({
            "stand_name": selected_stand["name"],
            "rarity": selected_stand["rarity"],
            "modifier": "Normal",
        }).eq(
            "twitch_id",
            twitch_id
        ).execute()
    return (
        f"{username}'s Stand has been set to "
        f"{selected_stand['name']} "
        f"[{selected_stand['rarity']}]!"
    )

    #
    # STAND SOUND
    #

@app.route("/standsound")
def get_stand_sound():

    twitch_id = request.args.get("twitch_id")
    secret = request.args.get("secret")

    if secret != API_SECRET:
        return "Unauthorized", 401

    if not twitch_id:
        return "Missing Twitch ID", 400

    # Find the user's Stand
    result = (
        supabase
        .table("stand_users")
        .select("stand_name")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    # User doesn't have a Stand
    if not result.data:
        return "NO_STAND", 404

    stand_name = result.data[0]["stand_name"]

    # Find that Stand in our editable list
    for stand in STANDS:

        if stand["name"] == stand_name:

            return stand["sound"]

    return "SOUND_NOT_FOUND", 404

# ============================================================
# RUN SERVER
# ============================================================

import threading


def start_streamelements_listener():
    asyncio.run(streamelements_listener())


if __name__ == "__main__":

    websocket_thread = threading.Thread(
        target=start_streamelements_listener,
        daemon=True
    )

    websocket_thread.start()

    app.run(
        host="0.0.0.0",
        port=5000
    )