import random

ACTIVE_BATTLES = {}


class StandBattle:

    def __init__(
        self,
        battle_id,
        player1,
        player2
    ):

        self.battle_id = battle_id

        self.player1 = player1
        self.player2 = player2

        self.player1_hp = 100
        self.player2_hp = 100

        self.turn = 1

        self.events = []

        self.finished = False
        self.winner = None

    def add_event(self, event):

        self.events.append(event)

    def attack(
        self,
        attacker,
        defender
    ):

        damage = random.randint(10, 25)

        if attacker == 1:

            self.player2_hp -= damage

            attacker_name = self.player1["username"]
            defender_name = self.player2["username"]

        else:

            self.player1_hp -= damage

            attacker_name = self.player2["username"]
            defender_name = self.player1["username"]

        self.add_event({
            "type": "attack",
            "attacker": attacker_name,
            "defender": defender_name,
            "damage": damage
        })

        self.check_winner()

    def check_winner(self):

        if self.player1_hp <= 0:

            self.player1_hp = 0

            self.finished = True
            self.winner = self.player2["username"]

        elif self.player2_hp <= 0:

            self.player2_hp = 0

            self.finished = True
            self.winner = self.player1["username"]

    def get_state(self):

        return {
            "battle_id": self.battle_id,

            "player1": self.player1,
            "player2": self.player2,

            "player1_hp": self.player1_hp,
            "player2_hp": self.player2_hp,

            "turn": self.turn,

            "events": self.events,

            "finished": self.finished,
            "winner": self.winner
        }


def create_battle(
    battle_id,
    player1,
    player2
):

    battle = StandBattle(
        battle_id,
        player1,
        player2
    )

    ACTIVE_BATTLES[battle_id] = battle

    return battle


def get_battle(battle_id):

    return ACTIVE_BATTLES.get(battle_id)


def remove_battle(battle_id):

    if battle_id in ACTIVE_BATTLES:
        del ACTIVE_BATTLES[battle_id]