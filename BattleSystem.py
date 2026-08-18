import random
import uuid


ACTIVE_BATTLE = None


BASE_HP = 100
BASE_ATTACK = 20
BASE_DEFENSE = 10
BASE_SPEED = 10


def create_fighter(username, twitch_id, stand_data):

    return {
        "username": username,
        "twitch_id": twitch_id,

        "stand_name": stand_data["stand_name"],
        "rarity": stand_data.get("rarity", "COMMON"),
        "modifier": stand_data.get("modifier", "Normal"),

        "max_hp": BASE_HP,
        "hp": BASE_HP,

        "attack": BASE_ATTACK,
        "defense": BASE_DEFENSE,
        "speed": BASE_SPEED,
    }


def calculate_damage(attacker, defender):

    variation = random.randint(-5, 5)

    damage = (
        attacker["attack"]
        + variation
        - defender["defense"]
    )

    damage = max(damage, 1)

    critical = random.random() < 0.10

    if critical:
        damage *= 2

    return damage, critical


def determine_first_attacker(fighter1, fighter2):

    if random.random() < 0.5:
        return fighter1, fighter2

    return fighter2, fighter1


def run_battle(player1, player2):

    global ACTIVE_BATTLE

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

    battle_id = str(uuid.uuid4())

    events = []

    # Battle introduction
    events.append({
        "type": "start",
        "text": (
            f"{fighter1['username']}'s "
            f"{fighter1['stand_name']} VS "
            f"{fighter2['username']}'s "
            f"{fighter2['stand_name']}!"
        )
    })

    attacker, defender = determine_first_attacker(
        fighter1,
        fighter2
    )

    round_number = 1

    while fighter1["hp"] > 0 and fighter2["hp"] > 0:

        damage, critical = calculate_damage(
            attacker,
            defender
        )

        defender["hp"] -= damage
        defender["hp"] = max(defender["hp"], 0)

        events.append({
            "type": "attack",

            "round": round_number,

            "attacker": attacker["username"],
            "attacker_stand": attacker["stand_name"],

            "defender": defender["username"],
            "defender_stand": defender["stand_name"],

            "damage": damage,
            "critical": critical,

            "player1_hp": fighter1["hp"],
            "player2_hp": fighter2["hp"],

            "text": (
                f"{attacker['stand_name']} attacks! "
                f"{defender['username']} takes {damage} damage!"
            )
        })

        if defender["hp"] <= 0:
            break

        attacker, defender = defender, attacker
        round_number += 1

        if round_number > 100:
            break

    if fighter1["hp"] > fighter2["hp"]:
        winner = fighter1
        loser = fighter2
    else:
        winner = fighter2
        loser = fighter1

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

    ACTIVE_BATTLE = {
        "battle_id": battle_id,

        "player1": {
            "username": fighter1["username"],
            "stand": fighter1["stand_name"],
            "max_hp": fighter1["max_hp"]
        },

        "player2": {
            "username": fighter2["username"],
            "stand": fighter2["stand_name"],
            "max_hp": fighter2["max_hp"]
        },

        "events": events,

        "current_event": 0,

        "finished": False
    }

    return ACTIVE_BATTLE


def get_active_battle():
    return ACTIVE_BATTLE