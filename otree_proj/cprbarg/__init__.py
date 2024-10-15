from otree.api import *
import random
from collections import deque


class C(BaseConstants):
    NAME_IN_URL = 'cprbarg'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 8
    BARGAINING_TIME = 180
    DISAGREEMENT_PAYOFF_P1 = 100
    DISAGREEMENT_PAYOFF_P2 = 400
    GROWTH_RATE = 1.7
    NUM_PERIODS = 2

    treatments = ["CZ", "NZ", "BZ", "CR", "NR", "BR"]
    CZ = "CPR, zero risk"
    CR = "CPR, w risk"
    NZ = "Non-binding bargaining, no risk"
    NR = "Non-binding bargaining, w risk"
    BZ = "Binding bargaining, no risk"
    BR = "Binding bargaining, w risk"

    RISK = {treatment: 0 if 'Z' in treatment else 0.5 for treatment in treatments}
    PIE_SIZE_T1 = 1000  # Initial pie size


class Subsession(BaseSubsession):
    treatment = models.StringField()
    sequence_order = models.StringField()

    def creating_session(self):
        selected_treatment = 'CR'
        selected_order = self.session.config.get('order', 'default_order')
        session_paid_round = random.randint(1, C.NUM_ROUNDS)
        pairs = self.get_pairs()

        for player in self.get_players():
            player.paid_round = session_paid_round
            player.treatment = selected_treatment
            player.sequence_order = selected_order
            player.current_round = self.round_number

        self.set_group_matrix(next(pairs))

    def get_pairs(self):
        nb_participants = len(self.get_players())
        PLAYERS1 = [p.id_in_subsession for p in self.get_players()[: nb_participants // 2]]
        PLAYERS2 = deque([p.id_in_subsession for p in self.get_players()[nb_participants // 2:]])

        while True:
            yield list(zip(PLAYERS1, PLAYERS2))
            PLAYERS2.rotate(1)


class Group(BaseGroup):
    total_extraction_t1 = models.FloatField(initial=0)  # Track total extraction in Period 1
    pie_size_t2 = models.FloatField(initial=C.PIE_SIZE_T1)  # Updated pie size for Period 2


class Player(BasePlayer):
    has_read_instructions = models.BooleanField(initial=False)
    paid_round = models.IntegerField()
    main_task_payoff = models.IntegerField()
    converted_payoff = models.IntegerField()
    total_payoff = models.CurrencyField()
    participation_fee = models.CurrencyField()
    current_round = models.IntegerField()
    treatment = models.StringField()
    sequence_order = models.StringField()

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
        treatment = player.field_maybe_none('treatment') or 'Unknown Treatment'
        risk = C.RISK.get(treatment, 0)
        print(f"TREATMENT: {treatment}, RISK: {risk}")

        return {
            'total_resource': f"Total resource in period 1: {C.PIE_SIZE_T1}",
            'max_extraction': max_extraction,  # We use max_extraction everywhere
            'risk_info': f"The possibility that the total resource will be wiped out and become 0 in the next period: {risk * 100}%"
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
            group.pie_size_t2 = max(0, C.PIE_SIZE_T1 - group.total_extraction_t1)


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
        treatment = player.field_maybe_none('treatment') or 'Unknown Treatment'
        risk = C.RISK.get(treatment, 0)
        # Check if a random event leads to the pie being reduced to 0
        if random.random() < risk:
            group.pie_size_t2 = 0
        else:
            group.pie_size_t2 = group.pie_size_t2  # Pie size remains the same

        return {
            'total_resource': f"Total resource in period 2: {group.pie_size_t2}",
            'max_extraction': max_extraction,  # Consolidate max_extraction
            'risk_info': f"The possibility that the total resource will be wiped out and become 0 in the next period: {risk * 100}%"
        }

    @staticmethod
    def error_message(player: Player, values):
        group = player.group
        max_extraction = group.pie_size_t2 / 2

        if player.id_in_group == 1:
            if values['extract_me_p1_t2'] > max_extraction:
                return f"You cannot extract more than {max_extraction} in Period 2."
            if values['guess_other_p1_t2'] > max_extraction:
                return f"You cannot guess more than {max_extraction} for the other participant's extraction."
        elif player.id_in_group == 2:
            if values['extract_me_p2_t2'] > max_extraction:
                return f"You cannot extract more than {max_extraction} in Period 2."
            if values['guess_other_p2_t2'] > max_extraction:
                return f"You cannot guess more than {max_extraction} for the other participant's extraction."


class Period1WaitPage(WaitPage):
    body_text = "Please wait for the other participant to finish."

    @staticmethod
    def after_all_players_arrive(group: Group):
        pass


class Period2WaitPage(WaitPage):
    body_text = "Please wait for the other participant to finish."

    @staticmethod
    def after_all_players_arrive(group: Group):
        pass


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


class FeedbackPeriod2(Page):
    @staticmethod
    def vars_for_template(player: Player):
        p1_extraction = player.group.get_player_by_id(1).field_maybe_none('extract_me_p1_t2') or 0
        p2_extraction = player.group.get_player_by_id(2).field_maybe_none('extract_me_p2_t2') or 0
        total_extraction = p1_extraction + p2_extraction
        remaining_pie = player.group.pie_size_t2 - total_extraction

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


page_sequence = [Period1, Period1WaitPage, FeedbackPeriod1, Period2, Period2WaitPage, FeedbackPeriod2]
