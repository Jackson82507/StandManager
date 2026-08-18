import random


# ============================================================
# BATTLE SETTINGS
# ============================================================

BASE_HP = 100

RARITY_STATS = {
    "COMMON": {
        "hp": 100,
        "attack": 15,
        "defense": 8,
        "speed": 10,
    },

    "UNCOMMON": {
        "hp": 105,
        "attack": 18,
        "defense": 10,
        "speed": 12,
    },

    "RARE": {
        "hp": 110,
        "attack": 22,
        "defense": 12,
        "speed": 14,
    },

    "EPIC": {
        "hp": 115,
        "attack": 26,
        "defense": 14,
        "speed": 16,
    },

    "LEGENDARY": {
        "hp": 120,
        "attack": 30,
        "defense": 16,
        "speed": 18,
    },

    "MYTHIC": {
        "hp": 130,
        "attack": 35,
        "defense": 18,
        "speed": 20,
    }
}


MODIFIER_BONUSES = {
    "Normal": {
        "hp": 0,
        "attack": 0,
        "defense": 0,
        "speed": 0,
    },

    "Shiny": {
        "hp": 5,
        "attack": 3,
        "defense": 2,
        "speed": 2,
    },

    "Rainbow": {
        "hp": 10,
        "attack": 6,
        "defense": 4,
        "speed": 4,
    },

    "Ethereal": {
        "hp": 15,
        "attack": 10,
        "defense": 6,
        "speed": 6,
    }
}


# ============================================================
# CREATE FIGHTER
# ============================================================

def create_fighter(username, twitch_id, stand_data):

    rarity = stand_data.get("rarity", "COMMON").upper()
    modifier = stand_data.get("modifier", "Normal")

    rarity_stats = RARITY_STATS.get(
        rarity,
        RARITY_STATS["COMMON"]
    )

    modifier_stats = MODIFIER_BONUSES.get(
        modifier,
        MODIFIER_BONUSES["Normal"]
    )

    hp = (
        rarity_stats["hp"]
        + modifier_stats["hp"]
    )

    attack = (
        rarity_stats["attack"]
        + modifier_stats["attack"]
    )

    defense = (
        rarity_stats["defense"]
        + modifier_stats["defense"]
    )

    speed = (
        rarity_stats["speed"]
        + modifier_stats["speed"]
    )

    return {
        "username": username,
        "twitch_id": twitch_id,

        "stand_name": stand_data["stand_name"],
        "rarity": rarity,
        "modifier": modifier,

        "max_hp": hp,
        "hp": hp,

        "attack": attack,
        "defense": defense,
        "speed": speed,
    }


# ============================================================
# DAMAGE
# ============================================================

def calculate_damage(attacker, defender):

    base_damage = attacker["attack"]

    variation = random.randint(
        -4,
        4
    )

    damage = (
        base_damage
        + variation
        - defender["defense"]
    )

    # Always do at least 1 damage
    damage = max(
        damage,
        1
    )

    # Critical hit
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

def determine_first_attacker(
    fighter1,
    fighter2
):

    if fighter1["speed"] > fighter2["speed"]:
        return fighter1, fighter2

    if fighter2["speed"] > fighter1["speed"]:
        return fighter2, fighter1

    # Same speed = random
    if random.random() < 0.5:
        return fighter1, fighter2

    return fighter2, fighter1


# ============================================================
# BATTLE
# ============================================================

def run_battle(
    player1,
    player2
):

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

    first, second = determine_first_attacker(
        fighter1,
        fighter2
    )

    attacker = first
    defender = second

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

        # Swap attacker
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