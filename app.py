import os
import random

from flask import Flask, request, jsonify
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_SECRET = os.getenv("API_SECRET")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


@app.route("/")
def home():
    return "Stand Power API is running!"


@app.route("/stand")
def get_stand():
    twitch_id = request.args.get("twitch_id")

    if not twitch_id:
        return "Missing Twitch ID", 400

    # Look for existing user
    result = (
        supabase
        .table("stand_users")
        .select("stand_power")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    # Existing user
    if result.data:
        power = result.data[0]["stand_power"]

        return f"🌀 Your Stand Power is {power}!"

    # New user
    power = random.randint(1, 100)

    supabase.table("stand_users").insert({
        "twitch_id": twitch_id,
        "stand_power": power
    }).execute()

    return f"🌀 You have been given a Stand Power of {power}!"


@app.route("/reroll")
def reroll():
    twitch_id = request.args.get("twitch_id")
    secret = request.args.get("secret")

    if secret != API_SECRET:
        return "Unauthorized", 401

    if not twitch_id:
        return "Missing Twitch ID", 400

    # Generate new power
    new_power = random.randint(1, 100)

    # Check whether user exists
    result = (
        supabase
        .table("stand_users")
        .select("twitch_id")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    if result.data:
        # Update existing Stand
        supabase.table("stand_users").update({
            "stand_power": new_power
        }).eq(
            "twitch_id", twitch_id
        ).execute()

    else:
        # Create Stand if they somehow don't have one
        supabase.table("stand_users").insert({
            "twitch_id": twitch_id,
            "stand_power": new_power
        }).execute()

    return f"🎲 Your Stand Power has been rerolled! New Power: {new_power}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)