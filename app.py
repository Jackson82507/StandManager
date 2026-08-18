from flask import Flask, request, jsonify, render_template
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
    run_battle,
    get_active_battle
)

@app.route("/")
def home():

    return "Stand Manager API is running!"

@app.route("/stand")
def get_stand():

    twitch_id = request.args.get("twitch_id")

    if not twitch_id:
        return "Missing Twitch ID", 400

    # Check if the user already has a Stand
    result = (
        supabase
        .table("stand_users")
        .select("stand_name, rarity, modifier")
        .eq("twitch_id", twitch_id)
        .execute()
    )

    # User already has a Stand
    if result.data:

        stand_name = result.data[0]["stand_name"]
        rarity = result.data[0]["rarity"]
        modifier = result.data[0]["modifier"] or "Normal"

        if modifier.lower() in ["normal", "none"]:
            return f"Your Stand is {stand_name}"

        return (
            f"Your Stand is {stand_name} "
            f"[{modifier}]"
        )

    # User doesn't have a Stand yet
    roll_result = roll_stand_for_user(twitch_id)

    stand = roll_result["stand"]
    modifier = roll_result["modifier"]

    stand_name = stand["name"]
    rarity = stand["rarity"]

    if modifier.lower() in ["normal", "none"]:
        return (
            f"You have received "
            f"{stand_name} [{rarity}]!"
        )

    return (
        f"You have received "
        f"{stand_name} [{rarity}] "
        f"[{modifier}]!"
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
        return "Reroll failed.", 500

    stand = result["stand"]
    modifier = result["modifier"]

    if modifier.lower() in ["normal", "none"]:
        message = (
            f"{username} rolled "
            f"{stand['name']} "
        )

    else:
        message = (
            f"{username} rolled "
            f"{stand['name']} "
            f"[{modifier}] "
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

@app.route("/battle")
def battle():

    twitch_id = request.args.get("twitch_id")
    username = request.args.get("username")
    opponent_username = request.args.get("opponent")
    secret = request.args.get("secret")

    if secret != API_SECRET:
        return "Unauthorized", 401

    if not twitch_id:
        return "Missing Twitch ID", 400

    if not username:
        return "Missing username", 400

    if not opponent_username:
        return "Missing opponent", 400

    # Prevent battling yourself
    if username.lower() == opponent_username.lower():
        return "You can't battle yourself!", 400

    # Get opponent Twitch ID
    opponent_id = get_twitch_user_id(
        opponent_username
    )

    if not opponent_id:
        return (
            f"Could not find Twitch user "
            f"{opponent_username}.",
            404
        )

    # Get both Stands
    player_stand = get_user_stand(
        twitch_id
    )

    opponent_stand = get_user_stand(
        opponent_id
    )

    print("BATTLE USERNAME:", username)
    print("BATTLE TWITCH ID:", twitch_id)

    player_stand = get_user_stand(twitch_id)

    print("PLAYER STAND RESULT:", player_stand)

    if not player_stand:
        return f"{username} doesn't have a Stand.", 400

    if not opponent_stand:
        return (
            f"{opponent_username} doesn't "
            f"have a Stand.",
            400
        )

    # Run battle
    result = run_battle(
        {
            "username": username,
            "twitch_id": twitch_id,
            "stand": player_stand,
        },

        {
            "username": opponent_username,
            "twitch_id": opponent_id,
            "stand": opponent_stand,
        }
    )

    winner = result["winner"]

    return (
        f"{username}'s "
        f"{player_stand['stand_name']} battled "
        f"{opponent_username}'s "
        f"{opponent_stand['stand_name']}! "
        f"{winner['username']} wins with "
        f"{winner['stand_name']}!"
    )

@app.route("/battle-screen")
def battle_screen():

    return render_template("battle.html")

@app.route("/battle-state")
def battle_state():

    battle = get_active_battle()

    if not battle:
        return jsonify({
            "active": False
        })

    return jsonify({
        "active": True,
        "battle": battle
    })

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )