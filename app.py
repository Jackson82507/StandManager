import os
import random
from pathlib import Path

from flask import Flask, request
from supabase import create_client
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_SECRET = os.getenv("API_SECRET")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
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
        "weight": 60
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
        "weight": 5
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


# ============================================================
# REROLL
# ============================================================

@app.route("/reroll")
def reroll():

    twitch_id = request.args.get("twitch_id")
    secret = request.args.get("secret")

    # Verify API secret
    if secret != API_SECRET:
        return "Unauthorized", 401

    if not twitch_id:
        return "Missing Twitch ID", 400

    # Generate new Stand
    stand = get_random_stand()

    stand_name = stand["name"]
    rarity = stand["rarity"]

    # Check whether user already exists
    result = (
        supabase
        .table("stand_users")
        .select("twitch_id")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    # --------------------------------------------------------
    # UPDATE EXISTING USER
    # --------------------------------------------------------

    if result.data:

        supabase.table("stand_users").update({
            "stand_name": stand_name,
            "rarity": rarity
        }).eq(
            "twitch_id",
            twitch_id
        ).execute()


    # --------------------------------------------------------
    # CREATE USER IF THEY DON'T EXIST
    # --------------------------------------------------------

    else:

        supabase.table("stand_users").insert({
            "twitch_id": twitch_id,
            "stand_name": stand_name,
            "rarity": rarity
        }).execute()


    return (
        f"🎲 Your Stand has been rerolled! "
        f"You received {stand_name} [{rarity}]!"
    )


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )