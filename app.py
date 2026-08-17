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

from StandSystem import (
    get_twitch_user_id,
    get_twitch_username_from_id,
    get_user_stand,
    roll_stand_for_user,
    reroll_stand,
    set_user_stand
)

from BattleSystem import (
    create_battle,
    get_battle
)

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
        .select("stand_name, rarity, modifier")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    if result.data:

        stand_name = result.data[0]["stand_name"]
        rarity = result.data[0]["rarity"]
        modifier = result.data[0]["modifier"]

        if modifier.lower() in ["normal", "none"]:
            message = (
                f"Your Stand is {stand_name}"
            )
        else:
            message = (
                f"Your Stand is {stand_name}"
                f" [{modifier}]"
            )

        return message

    stand = get_random_stand()

    stand_name = stand["name"]
    rarity = stand["rarity"]

    supabase.table("stand_users").insert({
        "twitch_id": twitch_id,
        "stand_name": stand_name,
        "rarity": rarity
    }).execute()

    return (
        f" You have received "
        f"{stand_name} [{rarity}]!"
    )


@app.route("/reroll")
def reroll():

    twitch_id = request.args.get("twitch_id")
    username = request.args.get("username")
    secret = request.args.get("secret")

    if secret != API_SECRET:
        return "Unauthorized", 401

    if not twitch_id:
        return "Missing Twitch ID", 400

    if not username:
        return "Missing username", 400

    result = (
        supabase
        .table("stand_users")
        .select("*")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    if not result.data:
        return "You don't have a Stand yet.", 400

    result = reroll_stand(twitch_id)

    if not result:
        return "❌ Reroll failed.", 500

    stand = result["stand_name"]
    modifier = result["modifier"]

    if modifier["name"].lower() in ["normal", "none"]:
        message = (
            f"{username} rolled "
            f"{stand['name']} "
            f"[{modifier['name']}] "
        )

    else:
        message = (
            f"{username} rolled "
            f"{stand['name']} "
            f"[{modifier['name']}] "
        )

    return message

@app.route("/setstandcommand")
def set_stand_command():

    username = request.args.get("username")
    stand_name = request.args.get("stand")
    secret = request.args.get("secret")

    if secret != API_SECRET:
        return "Unauthorized", 401

    if not username:
        return "Missing username", 400

    if not stand_name:
        return "Missing Stand name", 400

    stand_name = stand_name.replace("_", " ")

    selected_stand = None

    for stand in STANDS:

        if stand["name"].lower() == stand_name.lower():
            selected_stand = stand
            break

    if selected_stand is None:
        return f"Stand '{stand_name}' was not found.", 404

    twitch_id = get_twitch_user_id(username)

    if twitch_id is None:
        return f"Twitch user '{username}' was not found.", 404

    result = (
        supabase
        .table("stand_users")
        .select("twitch_id")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    if result.data:
        supabase.table("stand_users").update({
            "stand_name": selected_stand["name"],
            "rarity": selected_stand["rarity"],
            "modifier": "Normal",
        }).eq(
            "twitch_id",
            twitch_id
        ).execute()
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

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )