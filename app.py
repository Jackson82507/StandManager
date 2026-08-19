import os
import random
import requests
from supabase import create_client, Client

import secrets
from urllib.parse import urlencode

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session
)
import secrets

app = Flask(__name__)

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

app.secret_key = FLASK_SECRET_KEY

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_SECRET = os.getenv("API_SECRET")

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

TWITCH_REDIRECT_URI = os.getenv(
    "TWITCH_REDIRECT_URI"
)


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

from StandSystem import (
    get_twitch_user_id,
    get_twitch_username_from_id,
    get_user_stand,
    get_stand_inventory,
    add_stand_to_inventory,
    add_and_equip_stand,
    equip_stand,
    roll_stand_for_user,
    reroll_stand,
    set_user_stand
)

from BattleSystem import (
    run_battle,
    queue_battle,
    claim_active_battle,
    complete_active_battle,
    get_queue_size,
    clear_battles
)

@app.route("/")
def home():

    return render_template(
        "home.html",
        user=session.get("user")
    )

@app.route("/login")
def twitch_login():

    # Generate random state for security
    state = secrets.token_urlsafe(32)

    session["twitch_oauth_state"] = state

    params = {
        "client_id": TWITCH_CLIENT_ID,
        "redirect_uri": TWITCH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid",
        "state": state
    }

    twitch_auth_url = (
        "https://id.twitch.tv/oauth2/authorize?"
        + urlencode(params)
    )

    return redirect(twitch_auth_url)

@app.route("/auth/twitch/callback")
def twitch_callback():

    # ==========================================
    # CHECK FOR TWITCH ERROR
    # ==========================================

    error = request.args.get("error")

    if error:

        description = request.args.get(
            "error_description",
            "Twitch login failed."
        )

        return (
            f"Twitch login failed: {description}",
            400
        )


    # ==========================================
    # VERIFY STATE
    # ==========================================

    returned_state = request.args.get("state")

    expected_state = session.pop(
        "twitch_oauth_state",
        None
    )


    if (
        not returned_state
        or not expected_state
        or not secrets.compare_digest(
            returned_state,
            expected_state
        )
    ):

        return "Invalid OAuth state.", 400


    # ==========================================
    # GET AUTHORIZATION CODE
    # ==========================================

    code = request.args.get("code")

    if not code:
        return "Missing authorization code.", 400


    # ==========================================
    # EXCHANGE CODE FOR USER ACCESS TOKEN
    # ==========================================

    token_response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": TWITCH_REDIRECT_URI
        },
        timeout=10
    )


    if token_response.status_code != 200:

        print(
            "TWITCH TOKEN ERROR:",
            token_response.text
        )

        return "Could not log in with Twitch.", 500


    token_data = token_response.json()

    access_token = token_data.get(
        "access_token"
    )


    if not access_token:
        return "Twitch did not return an access token.", 500


    # ==========================================
    # GET TWITCH USER
    # ==========================================

    user_response = requests.get(
        "https://api.twitch.tv/helix/users",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Client-Id": TWITCH_CLIENT_ID
        },
        timeout=10
    )


    if user_response.status_code != 200:

        print(
            "TWITCH USER ERROR:",
            user_response.text
        )

        return "Could not retrieve Twitch user.", 500


    user_data = user_response.json().get(
        "data",
        []
    )


    if not user_data:
        return "Twitch user was not found.", 404


    twitch_user = user_data[0]


    # ==========================================
    # CREATE WEBSITE SESSION
    # ==========================================

    session["user"] = {
        "twitch_id": twitch_user["id"],
        "login": twitch_user["login"],
        "display_name": twitch_user["display_name"],
        "profile_image": twitch_user[
            "profile_image_url"
        ]
    }


    # ==========================================
    # GO TO DASHBOARD
    # ==========================================

    return redirect(
        url_for("dashboard")
    )

@app.route("/dashboard")
def dashboard():

    user = session.get("user")

    if not user:
        return redirect(
            url_for("twitch_login")
        )


    stand = get_user_stand(
        user["twitch_id"]
    )


    return render_template(
        "dashboard.html",
        user=user,
        stand=stand
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )

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

@app.route("/inventory")
def inventory():

    user = session.get("user")


    if not user:

        return redirect(
            url_for("twitch_login")
        )


    stands = get_stand_inventory(
        user["twitch_id"]
    )


    equipped_stand = get_user_stand(
        user["twitch_id"]
    )


    equipped_id = None


    if equipped_stand:

        equipped_id = (
            equipped_stand.get("id")
        )


    return render_template(
        "inventory.html",

        user=user,
        stands=stands,
        equipped_id=equipped_id
    )

@app.route(
    "/inventory/equip/<int:inventory_id>",
    methods=["POST"]
)
def equip_inventory_stand(
    inventory_id
):

    user = session.get("user")


    if not user:

        return redirect(
            url_for("twitch_login")
        )


    stand = equip_stand(
        user["twitch_id"],
        inventory_id
    )


    if not stand:

        return (
            "You don't own this Stand.",
            403
        )


    return redirect(
        url_for("inventory")
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

    if username.lower() == opponent_username.lower():
        return "You can't battle yourself!", 400

    # Get opponent Twitch ID
    opponent_id = get_twitch_user_id(opponent_username)

    if not opponent_id:
        return (
            f"Could not find Twitch user {opponent_username}.",
            404
        )

    # Get both users' Stands
    player_stand = get_user_stand(twitch_id)
    opponent_stand = get_user_stand(opponent_id)

    if not player_stand:
        return f"{username} doesn't have a Stand.", 400

    if not opponent_stand:
        return f"{opponent_username} doesn't have a Stand.", 400

    # Run the battle
    battle_data = run_battle(
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

    if not battle_data:
        return "Battle failed.", 500

    queue_position = queue_battle(
        battle_data
    )

    if queue_position == 0:
        return (
            f"{username}'s "
            f"{player_stand['stand_name']} VS "
            f"{opponent_username}'s "
            f"{opponent_stand['stand_name']} "
            f"is starting!"
        )

    return (
        f"{username}'s "
        f"{player_stand['stand_name']} VS "
        f"{opponent_username}'s "
        f"{opponent_stand['stand_name']} "
        f"has been queued! "
        f"Queue position: {queue_position}"
    )

    if not result:
        return "Battle failed.", 500

    winner_event = result["events"][-1]

    return (
        f"{username}'s "
        f"{player_stand['stand_name']} battled "
        f"{opponent_username}'s "
        f"{opponent_stand['stand_name']}! "
        f"{winner_event['winner']} wins with "
        f"{winner_event['winner_stand']}!"
    )


@app.route("/battle-screen")
def battle_screen():
    return render_template("battle.html")


@app.route("/battle-state")
def battle_state():

    battle = claim_active_battle()

    if not battle:

        return jsonify({
            "active": False
        })

    return jsonify({
        "active": True,
        "battle": battle
    })

@app.route("/battle-complete", methods=["POST"])
def battle_complete():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "error": "Missing JSON"
        }), 400


    battle_id = data.get(
        "battle_id"
    )


    if not battle_id:

        return jsonify({
            "success": False,
            "error": "Missing battle ID"
        }), 400


    success = complete_active_battle(
        battle_id
    )


    return jsonify({
        "success": success,
        "queue_size": get_queue_size()
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )