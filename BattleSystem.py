import random
import uuid


# ============================================================
# GLOBAL ACTIVE BATTLE
# ============================================================

ACTIVE_BATTLE = None


# ============================================================
# BASE BATTLE SETTINGS
# ============================================================

BASE_HP = 100
BASE_ATTACK = 20
BASE_DEFENSE = 10
BASE_SPEED = 10

CRITICAL_CHANCE = 0.10


# ============================================================
# CREATE FIGHTER
# ============================================================

def create_fighter(
    username,
    twitch_id,
    stand_data
):

    return {
        "username": username,
        "twitch_id": twitch_id,

        # Stand information
        "stand_name": stand_data["stand_name"],

        # We keep these for display/use later,
        # but they do NOT affect battle stats yet.
        "rarity": stand_data.get(
            "rarity",
            "COMMON"
        ),

        "modifier": stand_data.get(
            "modifier",
            "Normal"
        ),

        # Base combat stats
        "max_hp": BASE_HP,
        "hp": BASE_HP,

        "attack": BASE_ATTACK,
        "defense": BASE_DEFENSE,
        "speed": BASE_SPEED,
    }


# ============================================================
# DAMAGE CALCULATION
# ============================================================

def calculate_damage(
    attacker,
    defender
):

    # Small random variation so attacks aren't identical
    variation = random.randint(
        -5,
        5
    )

    damage = (
        attacker["attack"]
        + variation
        - defender["defense"]
    )

    # Never deal less than 1 damage
    damage = max(
        damage,
        1
    )

    # Critical hit
    critical = (
        random.random()
        < CRITICAL_CHANCE
    )

    if critical:
        damage *= 2

    return damage, critical


# ============================================================
# DETERMINE WHO GOES FIRST
# ============================================================

def determine_first_attacker(
    fighter1,
    fighter2
):

    # Later you can make Stand speed matter.
    # For now both fighters have equal speed,
    # so choose randomly.

    if random.random() < 0.5:
        return fighter1, fighter2

    return fighter2, fighter1


# ============================================================
# RUN BATTLE
# ============================================================

def run_battle(
    player1,
    player2
):

    global ACTIVE_BATTLE


    # --------------------------------------------------------
    # CREATE FIGHTERS
    # --------------------------------------------------------

    fighter1 = create_fighter(
        player1["username"],
        player1["twitch_id"],
        player1["stand"]
    )

    fighter2 = create_fighter(
        player2["username"],
        player2["twitch_id"],
        player2["stand"]
    )


    battle_id = str(
        uuid.uuid4()
    )

    events = []


    # --------------------------------------------------------
    # BATTLE START EVENT
    # --------------------------------------------------------

    events.append({
        "type": "start",

        "player1": fighter1["username"],
        "player1_stand": fighter1["stand_name"],

        "player2": fighter2["username"],
        "player2_stand": fighter2["stand_name"],

        "player1_hp": fighter1["hp"],
        "player2_hp": fighter2["hp"],

        "text": (
            f"{fighter1['username']}'s "
            f"{fighter1['stand_name']} VS "
            f"{fighter2['username']}'s "
            f"{fighter2['stand_name']}!"
        )
    })


    # --------------------------------------------------------
    # CHOOSE FIRST ATTACKER
    # --------------------------------------------------------

    attacker, defender = (
        determine_first_attacker(
            fighter1,
            fighter2
        )
    )


    round_number = 1


    # --------------------------------------------------------
    # BATTLE LOOP
    # --------------------------------------------------------

    while (
        fighter1["hp"] > 0
        and fighter2["hp"] > 0
    ):

        damage, critical = (
            calculate_damage(
                attacker,
                defender
            )
        )


        # Apply damage
        defender["hp"] -= damage

        defender["hp"] = max(
            defender["hp"],
            0
        )


        # ----------------------------------------------------
        # CREATE ATTACK TEXT
        # ----------------------------------------------------

        if critical:

            attack_text = (
                f"{attacker['stand_name']} attacks! "
                f"CRITICAL HIT! "
                f"{defender['username']} takes "
                f"{damage} damage!"
            )

        else:

            attack_text = (
                f"{attacker['stand_name']} attacks! "
                f"{defender['username']} takes "
                f"{damage} damage!"
            )


        # ----------------------------------------------------
        # STORE ATTACK EVENT
        # ----------------------------------------------------

        events.append({
            "type": "attack",

            "round": round_number,

            "attacker": attacker["username"],
            "attacker_stand": attacker["stand_name"],

            "defender": defender["username"],
            "defender_stand": defender["stand_name"],

            "damage": damage,
            "critical": critical,

            # Important for OBS HP bars
            "player1_hp": fighter1["hp"],
            "player2_hp": fighter2["hp"],

            "text": attack_text
        })


        # ----------------------------------------------------
        # CHECK FOR KO
        # ----------------------------------------------------

        if defender["hp"] <= 0:
            break


        # ----------------------------------------------------
        # SWITCH TURNS
        # ----------------------------------------------------

        attacker, defender = (
            defender,
            attacker
        )

        round_number += 1


        # Safety in case something ever goes wrong
        if round_number > 100:
            break


    # --------------------------------------------------------
    # DETERMINE WINNER
    # --------------------------------------------------------

    if fighter1["hp"] > fighter2["hp"]:

        winner = fighter1
        loser = fighter2

    elif fighter2["hp"] > fighter1["hp"]:

        winner = fighter2
        loser = fighter1

    else:

        # Extremely unlikely, but handles a draw safely
        winner = random.choice([
            fighter1,
            fighter2
        ])

        if winner is fighter1:
            loser = fighter2
        else:
            loser = fighter1


    # --------------------------------------------------------
    # VICTORY EVENT
    # --------------------------------------------------------

    events.append({
        "type": "victory",

        "winner": winner["username"],
        "winner_stand": winner["stand_name"],

        "loser": loser["username"],
        "loser_stand": loser["stand_name"],

        "player1_hp": fighter1["hp"],
        "player2_hp": fighter2["hp"],

        "text": (
            f"{winner['username']} wins with "
            f"{winner['stand_name']}!"
        )
    })


    # --------------------------------------------------------
    # SAVE CURRENT BATTLE FOR OBS
    # --------------------------------------------------------

    ACTIVE_BATTLE = {

        "battle_id": battle_id,

        "player1": {
            "username": fighter1["username"],
            "twitch_id": fighter1["twitch_id"],
            "stand": fighter1["stand_name"],

            "rarity": fighter1["rarity"],
            "modifier": fighter1["modifier"],

            "max_hp": fighter1["max_hp"]
        },

        "player2": {
            "username": fighter2["username"],
            "twitch_id": fighter2["twitch_id"],
            "stand": fighter2["stand_name"],

            "rarity": fighter2["rarity"],
            "modifier": fighter2["modifier"],

            "max_hp": fighter2["max_hp"]
        },

        "events": events,

        "finished": True
    }


    return ACTIVE_BATTLE

def get_active_battle():
    return ACTIVE_BATTLE


def consume_active_battle():

    global ACTIVE_BATTLE

    if ACTIVE_BATTLE is None:
        return None

    battle = ACTIVE_BATTLE

    # Remove it immediately
    ACTIVE_BATTLE = None

    return battle


def clear_active_battle():

    global ACTIVE_BATTLE
    ACTIVE_BATTLE = None