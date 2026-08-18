import random


# ============================================================
# BATTLE SETTINGS
# ============================================================

BASE_HP = 100
BASE_ATTACK = 20
BASE_DEFENSE = 10
BASE_SPEED = 10


# ============================================================
# CREATE FIGHTER
# ============================================================

def create_fighter(username, twitch_id, stand_data):

    return {
        "username": username,
        "twitch_id": twitch_id,

        "stand_name": stand_data["stand_name"],

        # Stored for display only
        "rarity": stand_data.get("rarity", "COMMON"),
        "modifier": stand_data.get("modifier", "Normal"),

        # Battle stats do NOT use rarity/modifier
        "max_hp": BASE_HP,
        "hp": BASE_HP,

        "attack": BASE_ATTACK,
        "defense": BASE_DEFENSE,
        "speed": BASE_SPEED,
    }


# ============================================================
# DAMAGE
# ============================================================

def calculate_damage(attacker, defender):

    variation = random.randint(-5, 5)

    damage = (
        attacker["attack"]
        + variation
        - defender["defense"]
    )

    damage = max(damage, 1)

    # 10% crit chance
    critical = random.random() < 0.10

    if critical:
        damage *= 2

    return damage, critical


# ============================================================
# ATTACK
# ============================================================

def attack(attacker, defender):

    damage, critical = calculate_damage(
        attacker,
        defender
    )

    defender["hp"] -= damage

    if defender["hp"] < 0:
        defender["hp"] = 0

    return {
        "type": "attack",

        "attacker": attacker["username"],
        "attacker_stand": attacker["stand_name"],

        "defender": defender["username"],
        "defender_stand": defender["stand_name"],

        "damage": damage,
        "critical": critical,

        "defender_hp": defender["hp"],
        "defender_max_hp": defender["max_hp"],
    }


# ============================================================
# TURN ORDER
# ============================================================

def determine_first_attacker(fighter1, fighter2):

    # Since everyone currently has the same speed,
    # randomly choose who goes first.

    if random.random() < 0.5:
        return fighter1, fighter2

    return fighter2, fighter1


# ============================================================
# RUN BATTLE
# ============================================================

def run_battle(player1, player2):

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

    events = []

    attacker, defender = determine_first_attacker(
        fighter1,
        fighter2
    )

    round_number = 1

    while (
        fighter1["hp"] > 0
        and fighter2["hp"] > 0
    ):

        event = attack(
            attacker,
            defender
        )

        event["round"] = round_number

        events.append(event)

        if defender["hp"] <= 0:
            break

        attacker, defender = (
            defender,
            attacker
        )

        round_number += 1

        # Safety limit
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
    })

    return {
        "fighter1": fighter1,
        "fighter2": fighter2,

        "winner": winner,
        "loser": loser,

        "events": events,
    }