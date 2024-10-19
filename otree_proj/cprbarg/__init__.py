from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = 'cprbarg'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 8
    BARGAINING_TIME = 180
    GROWTH_RATE = 1.5  # Resource growth rate
    NUM_PERIODS = 2
    RISK = 0.5  # Set risk to 50% for all participants
    PIE_SIZE_T1 = 1000  # Initial pie size


class Subsession(BaseSubsession):
    def creating_session(self):
        for player in self.get_players():
            player.current_round = self.round_number
        # Set the initial grouping for round 1
        self.set_stranger_matching()

    def set_stranger_matching(self):
        """Shuffles players and assigns new groups each round."""
        players = self.get_players()
        random.shuffle(players)  # Randomly shuffle players for stranger matching

        group_matrix = [players[i:i + C.PLAYERS_PER_GROUP] for i in range(0, len(players), C.PLAYERS_PER_GROUP)]
        self.set_group_matrix(group_matrix)


class Group(BaseGroup):
    total_extraction_t1 = models.FloatField(initial=0)  # Track total extraction in Period 1
    pie_size_t2 = models.FloatField(initial=C.PIE_SIZE_T1)  # Updated pie size for Period 2

    def update_pie_size_t2(self):
        remaining_pie = C.PIE_SIZE_T1 - self.total_extraction_t1
        self.pie_size_t2 = remaining_pie * C.GROWTH_RATE  # Apply growth rate to remaining pie


class Player(BasePlayer):
    has_read_instructions = models.BooleanField(initial=False)
    paid_round = models.IntegerField()
    main_task_payoff = models.IntegerField()
    converted_payoff = models.IntegerField()
    total_payoff = models.CurrencyField()
    participation_fee = models.CurrencyField()
    current_round = models.IntegerField()

    # Separate extraction and guessing fields for P1 and P2 in Period 1 and Period 2
    extract_me_p1_t1 = models.FloatField(min=0)
    guess_other_p1_t1 = models.FloatField(min=0)
    extract_me_p2_t1 = models.FloatField(min=0)
    guess_other_p2_t1 = models.FloatField(min=0)

    extract_me_p1_t2 = models.FloatField(min=0)  # Period 2 fields
    guess_other_p1_t2 = models.FloatField(min=0)
    extract_me_p2_t2 = models.FloatField(min=0)
    guess_other_p2_t2 = models.FloatField(min=0)


class Period1(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player: Player):
        if player.id_in_group == 1:
            return ['extract_me_p1_t1', 'guess_other_p1_t1']
        elif player.id_in_group == 2:
            return ['extract_me_p2_t1', 'guess_other_p2_t1']

    @staticmethod
    def vars_for_template(player: Player):
        max_extraction = C.PIE_SIZE_T1 / 2  # Maximum extraction for Period 1
        return {
            'total_resource': f"Total resource: {C.PIE_SIZE_T1}",
            'max_extraction': max_extraction,
            'growth_rate': f"The resource growth rate: {(C.GROWTH_RATE - 1) * 100}%",
            'risk_info': f"The possibility that the total resource will be wiped out and become 0 in the next period: {C.RISK * 100}%",
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        group = player.group
        if player.id_in_group == 1:
            group.total_extraction_t1 += player.extract_me_p1_t1
        elif player.id_in_group == 2:
            group.total_extraction_t1 += player.extract_me_p2_t1

        # Update the pie size for Period 2 (after deduction)
        if player.round_number == 1:
            group.update_pie_size_t2()  # Apply the correct logic to update pie size for Period 2


class Period1WaitPage(WaitPage):
    body_text = "Please wait for the other participant to finish."

    @staticmethod
    def after_all_players_arrive(group: Group):
            remaining_pie = C.PIE_SIZE_T1 - group.total_extraction_t1
            if random.random() < C.RISK:
                group.pie_size_t2 = 0  # Apply risk, pie becomes 0
            else:
                group.pie_size_t2 = remaining_pie * C.GROWTH_RATE


class FeedbackPeriod1(Page):
    @staticmethod
    def vars_for_template(player: Player):
        p1_extraction = player.group.get_player_by_id(1).field_maybe_none('extract_me_p1_t1') or 0
        p2_extraction = player.group.get_player_by_id(2).field_maybe_none('extract_me_p2_t1') or 0
        total_extraction = p1_extraction + p2_extraction
        remaining_pie = C.PIE_SIZE_T1 - total_extraction

        if player.id_in_group == 1:
            message = f"You have extracted: {p1_extraction}.<br>The other participant has extracted: {p2_extraction}.<br>Remaining pie: {remaining_pie}."
        else:
            message = f"You have extracted: {p2_extraction}.<br>The other participant has extracted: {p1_extraction}.<br>Remaining pie: {remaining_pie}."

        return {
            'message': message,
            'your_extraction': p1_extraction if player.id_in_group == 1 else p2_extraction,
            'other_extraction': p2_extraction if player.id_in_group == 1 else p1_extraction,
            'remaining_pie': remaining_pie,
        }


class Period2(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player: Player):
        if player.id_in_group == 1:
            return ['extract_me_p1_t2', 'guess_other_p1_t2']
        elif player.id_in_group == 2:
            return ['extract_me_p2_t2', 'guess_other_p2_t2']

    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        max_extraction = group.pie_size_t2 / 2  # Maximum extraction for Period 2

        return {
            'total_resource': f"Total resource: {group.pie_size_t2}",
            'max_extraction': max_extraction,
            'growth_rate': f"The resource growth rate: {(C.GROWTH_RATE - 1) * 100}%",
            'risk_info': f"The possibility that the total resource will be wiped out and become 0 in the next period: {C.RISK * 100}%",
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # No need to update pie size here, as it will be handled after all players arrive on the wait page.
        pass


class Period2WaitPage(WaitPage):
    body_text = "Please wait for the other participant to finish."

    @staticmethod
    def after_all_players_arrive(group: Group):
        pass


class FeedbackPeriod2(Page):
    @staticmethod
    def vars_for_template(player: Player):
        # Get the updated pie size after growth and risk adjustments in the wait page
        group = player.group

        # Period 2 extraction amounts
        p1_extraction = group.get_player_by_id(1).field_maybe_none('extract_me_p1_t2') or 0
        p2_extraction = group.get_player_by_id(2).field_maybe_none('extract_me_p2_t2') or 0

        # Calculate the total extraction for Period 2 and the remaining pie size
        total_extraction = p1_extraction + p2_extraction
        remaining_pie = group.pie_size_t2 - total_extraction  # Use updated pie size from Period 2

        # Display feedback based on the player's ID
        if player.id_in_group == 1:
            message = f"You have extracted: {p1_extraction}.<br>The other participant has extracted: {p2_extraction}.<br>Remaining pie: {remaining_pie}."
        else:
            message = f"You have extracted: {p2_extraction}.<br>The other participant has extracted: {p1_extraction}.<br>Remaining pie: {remaining_pie}."

        return {
            'message': message,
            'your_extraction': p1_extraction if player.id_in_group == 1 else p2_extraction,
            'other_extraction': p2_extraction if player.id_in_group == 1 else p1_extraction,
            'remaining_pie': remaining_pie,  # Remaining pie after all extractions
        }


class BeforeNextRoundWaitPage(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        """Stranger matching and reset before each new round."""
        # Shuffle and reassign players to new groups
        subsession.set_stranger_matching()

        # Reset conditions for each new round
        for group in subsession.get_groups():
            # Reset the pie size for the next round to the initial value
            group.pie_size_t2 = C.PIE_SIZE_T1

            # Reset the total extraction for Period 1
            group.total_extraction_t1 = 0


page_sequence = [
    Period1,
    Period1WaitPage,
    FeedbackPeriod1,
    Period2,
    Period2WaitPage,  # Ensure players are synced in Period 2
    FeedbackPeriod2,
    BeforeNextRoundWaitPage
]
