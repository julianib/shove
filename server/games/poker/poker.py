from server_util import *
from base_game import BaseGame
from player import Player
from .deuces_custom import Card, Deck, Evaluator


# todo it is supposed to be called holdem


STREET_PREFLOP = "PREFLOP"
STREET_FLOP = "FLOP"
STREET_TURN = "TURN"
STREET_RIVER = "RIVER"


class NoMoreStreets(Exception):
    pass


class StreetEnded(Exception):
    pass


class Poker(BaseGame):
    def __init__(self, table):
        super().__init__(table)
        self.small_blind_amount = 1

        self.action_seat: int = 0
        self.big_blind_amount = 2 * self.small_blind_amount
        self.big_blind_seat = 0
        self.community_cards: List[int] = []
        self.dealer_seat = 0
        self.deck: Deck = Deck()
        self.highest_bet_this_street = 0
        self.n_hands_played = 0
        self.players = []
        self.pot = None  # todo temp, actual pot management and splitting soon
        # self.pots = {}
        self.small_blind_seat = 0
        self.street = None

        self.total_elapsed = 0  # testing purposes

    def do_action(self):
        action_player = self.get_player_in_seat(self.action_seat)
        to_call = self.highest_bet_this_street - action_player["bet"]
        Log.info(f"Action on {action_player}, to call: {to_call}")

        if action_player.is_bot:
            # todo generate action should just access table.game.X instead, dont pass all data
            action_player.generate_bot_decision(to_call, self.highest_bet_this_street, self.big_blind_amount)

            if action_player["bet"] > self.highest_bet_this_street:
                self.highest_bet_this_street = action_player["bet"]

                for player in self.players:
                    if player == action_player:
                        continue

                    player["manual_bet_matches"] = False

        else:  # todo abstract player object should have connection socket (and Account object?)
            for connection, player in self.table.server.connections_players.items():
                if action_player == player:
                    self.table.server.outgoing_packets.put((connection, {
                        "model": "action",
                        "street": self.street,
                        "players": self.players
                    }))

    def add_bets_to_pots(self):
        Log.trace("Adding bets to pots")

        for player in self.players:
            self.pot += player["bet"]
            player["bet"] = 0

        # lowest_bet = 0  # todo broken
        #
        # player_bets_remaining = {player: player["bet"] for player in self.players}
        #
        # pot_number = 0
        # while player_bets_remaining:  # there are still bets left to process and add to pot
        #     players_in_pot = list(player_bets_remaining.keys())
        #     if len(players_in_pot) == 1:
        #
        #         log(f"Returned {player_bets_remaining[player]} excess chips to {player}")
        #         break
        #
        #     pot_number += 1
        #     self.pots[pot_number] = {"players": [], "size": 0}
        #
        #     log(f"Created pot number {pot_number}")
        #
        #     for player, bet in player_bets_remaining.items():
        #         if bet < lowest_bet or not lowest_bet:
        #             lowest_bet = bet
        #
        #     log(f"Lowest bet: {lowest_bet}")
        #     self.pots[pot_number]["players"] = players_in_pot
        #     self.pots[pot_number]["size"] = lowest_bet * len(players_in_pot)
        #     log(f"Pot size: {self.pots[pot_number]['size']}")
        #
        #     for player, bet in player_bets_remaining.items():
        #         player_bets_remaining[player] -= lowest_bet
        #         if not player_bets_remaining[player]:  # all player's chips have been added to pot
        #             log(f"Collected all chips of {player}")
        #             del player_bets_remaining[player]

        Log.info(f"Total pot: {self.pot}")

    def deal_community_cards_for_street(self, street, deal_all_streets=False):
        if deal_all_streets:
            Log.trace("Dealing all streets (DEBUG ONLY)")
            for street in [STREET_FLOP, STREET_TURN, STREET_RIVER]:
                self.deal_community_cards_for_street(street)

            Log.trace("Done dealing all streets")
            return

        if street == STREET_FLOP:
            n_cards = 3
        else:
            n_cards = 1

        drawn_cards = self.deck.draw(n_cards)
        self.community_cards.extend(drawn_cards)
        # todo send a packet here with only the newly drawn cards, not including all the old ones

        Log.info(f"Dealt community cards: {Card.get_pretty_str(self.community_cards)}")

    def deal_player_cards(self):
        Log.trace("Dealing cards to players")

        for player in self.players:
            drawn_cards = self.deck.draw(2)
            player["cards"] = drawn_cards
            Log.debug(f"Dealt cards to {player}: {Card.get_pretty_str(drawn_cards)}")

        Log.info("Dealt cards to players")

    def get_next_action_seat(self, start_seat, last_action_seat) -> int:
        """Returns 0 if betting is over"""

        Log.debug("Getting next action seat")
        seats = self.get_seats()
        assert start_seat in seats and last_action_seat in seats, "no valid start/last_action seat"

        # reorder player list to check in order, starting at player in seat start_seat, excl. last action player
        players_cycled = self.players.copy()
        while players_cycled[0]["seat"] != start_seat:  # should never be an infinite loop
            players_cycled.append(players_cycled.pop(0))

        for player in players_cycled:
            if player["seat"] == last_action_seat:
                Log.trace(f"Skipped {player} for action: last action seat")
                continue

            if player["manual_bet_matches"] and self.highest_bet_this_street:
                Log.trace(f"Skipped {player} for action: manual bet matches")
                continue

            if player["all_in"]:
                Log.trace(f"Skipped {player} for action: is all-in")
                continue

            if player["folded"]:
                Log.trace(f"Skipped {player} for action: has folded")
                continue

            player_seat = player["seat"]
            Log.debug(f"Got next action seat: {player_seat}")
            return player_seat

        Log.debug("Betting is over")
        return 0

    def get_next_street(self):
        if self.street is None:
            self.street = STREET_PREFLOP

        elif self.street == STREET_PREFLOP:
            self.street = STREET_FLOP

        elif self.street == STREET_FLOP:
            self.street = STREET_TURN

        elif self.street == STREET_TURN:
            self.street = STREET_RIVER

        elif self.street == STREET_RIVER:
            raise NoMoreStreets

        if self.street in [STREET_FLOP, STREET_TURN, STREET_RIVER]:
            self.deal_community_cards_for_street(self.street)

        return self.street

    def get_not_folded_players(self):
        return [player for player in self.players if not player["folded"]]

    def get_player_in_seat(self, seat: int) -> Player:
        for player in self.players:
            if player["seat"] == seat:
                return player

        Log.error(f"No player in seat: {seat}")

    def get_seats(self):
        return [player["seat"] for player in self.players]

    def handle_event(self, event):
        pass

    def on_showdown(self):  # todo handle side pots
        Log.info(f"Showdown started")

        players = self.get_not_folded_players()

        evaluator = Evaluator()
        winners, best_hand = evaluator.get_winners(self.community_cards, players)

        Log.info(f"Pot winners: {winners} with {best_hand}")

        chips_won_fraction = int(self.pot / len(winners))  # todo give last aggressor the chip if uneven
        for winner in winners:
            winner.won_chips(chips_won_fraction)

        # tracking what pocket pairs eventually win the most hands
        for player in players:
            cards = player["cards"]
            rank_ints = []
            suit_ints = []
            for card in cards:
                rank_ints.append(Card.get_rank_int(card))
                suit_ints.append(Card.get_suit_int(card))

            if rank_ints[0] < rank_ints[1]:
                rank_ints.append(rank_ints.pop(0))

            suited = suit_ints[0] == suit_ints[1]
            pair = rank_ints[0] == rank_ints[1]

            if pair:
                suffix = ""
            else:
                if suited:
                    suffix = "s"
                else:
                    suffix = "o"

            cards_formatted = f"{Card.STR_RANKS[rank_ints[0]]}{Card.STR_RANKS[rank_ints[1]]}{suffix}"

            with open("pocket_cards.json", "r") as f:
                pocket_cards = json.load(f)

            pocket_cards[cards_formatted]["times_dealt"] += 1
            Log.test(f"incremented times dealt of {cards_formatted}")

            if player in winners:
                pocket_cards[cards_formatted]["times_won"] += 1
                Log.test(f"incremented times won of {cards_formatted}")

            with open("pocket_cards.json", "w") as f:
                json.dump(pocket_cards, f, indent=4)

    def post_blinds(self):
        # assert self.n_taken_seats() >= 2, "need 2 or more players to place blinds"  # safety check

        Log.debug(f"Posting blinds")
        small_blind_player = self.get_player_in_seat(self.small_blind_seat)
        big_blind_player = self.get_player_in_seat(self.big_blind_seat)

        small_blind_player.post_blind(self.small_blind_amount)
        big_blind_player.post_blind(self.big_blind_amount)

        self.highest_bet_this_street = 2

    def reset_pot(self):  # todo reset pot manager
        self.pot = 0

    def start(self):  # todo is only called once (as soon as enough players at table)
        self.players = sorted([player for player in self.table.seats_players.values()
                               if player is not None and
                               player["chips"] > 0],
                              key=lambda p: p["seat"], reverse=False)

        if len(self.players) < 2:
            Log.warn("Not enough players with chips to start")
            return

        self.running = True
        self.start_hand()

    def start_hand(self):  # todo starts new hand, moves dealer button, etc.
        # hand progression explained:
        # https://www.instructables.com/Learn-To-Play-Poker---Texas-Hold-Em-aka-Texas-Ho/

        self.n_hands_played += 1
        start_time = time.time()
        Log.info(f"Hand #{self.n_hands_played} started! Players: {self.players}")

        for player in self.players:
            player.new_hand_starting()

        self.street = None
        self.community_cards = []
        self.deck = Deck()
        self.deck.shuffle()
        self.reset_pot()
        self.update_dealer_blind_action_seats()
        self.post_blinds()
        self.deal_player_cards()
        street = self.get_next_street()  # sets to PREFLOP if necessary
        Log.info(f"Betting started: {street}")

        seats = self.get_seats()
        while self.action_seat:
            self.do_action()

            # start looking for next action-eligible player at seat after the seat who just had action
            start_seat = seats[(seats.index(self.action_seat) + 1) % len(seats)]
            self.action_seat = self.get_next_action_seat(start_seat, self.action_seat)

        self.add_bets_to_pots()
        self.deal_community_cards_for_street(STREET_FLOP, deal_all_streets=True)
        self.on_showdown()
        elapsed_time = time.time() - start_time
        Log.info(f"Hand finished in {elapsed_time}!")
        self.total_elapsed += elapsed_time
        Log.test(f"Hands: {self.n_hands_played}, average time: {round(self.total_elapsed / self.n_hands_played * 1000)}ms")
        self.running = False

    def update_dealer_blind_action_seats(self):
        # if self.n_taken_seats() < 2:  # safety check
        #     log(f"Ignoring update dealer/blinds call with < 2 players", LEVEL_ERROR)
        #     return

        # todo players new to table always pay big blind

        Log.debug(f"Updating dealer and blind seats")
        seats = self.get_seats()
        n_seats = len(seats)
        old_dealer_seat = self.dealer_seat

        if not old_dealer_seat:  # dealer/blind seats not set
            new_dealer_seat_index = random.randint(0, n_seats - 1)

        else:
            new_dealer_seat_index = 0  # not changed if old dealer seat was the last occupied seat
            for i, seat in enumerate(seats):
                if seat > old_dealer_seat:
                    new_dealer_seat_index = i
                    break

        new_dealer_seat = seats[new_dealer_seat_index]
        self.dealer_seat = new_dealer_seat

        if n_seats == 2:  # in heads up the dealer is the small blind
            Log.trace("Selecting blind/action seats for heads up")
            self.small_blind_seat = new_dealer_seat
            self.big_blind_seat = seats[(new_dealer_seat_index + 1) % n_seats]
            self.action_seat = new_dealer_seat  # todo take into account if player is not active
        else:
            Log.trace("Selecting blind/action seats for non-heads up")
            self.small_blind_seat = seats[(new_dealer_seat_index + 1) % n_seats]
            self.big_blind_seat = seats[(new_dealer_seat_index + 2) % n_seats]
            self.action_seat = seats[(new_dealer_seat_index + 3) % n_seats]  # todo take into account if player is not active

        if old_dealer_seat > 0:
            old_dealer_seat_formatted = old_dealer_seat
        else:
            old_dealer_seat_formatted = "(not set)"

        Log.info(f"Updated seats, D: {old_dealer_seat_formatted} -> {new_dealer_seat}, SB: {self.small_blind_seat}, BB: {self.big_blind_seat}")
