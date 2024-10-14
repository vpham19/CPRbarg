import os

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.01,  # 1 point = 0.01 in real-world currency
    participation_fee=10.00,  # Flat participation fee for each player
    doc="Default session configuration",  # Documentation or description for your session
)

SESSION_CONFIGS = [
    dict(
        name='cpr_bargaining',  # Name of the session
        display_name="CPR Bargaining Game",
        num_demo_participants=4,  # Number of demo participants
        app_sequence=['cprbarg'],  # List of apps (this should match the app's directory name)
        order='default_order',  # Custom configuration parameter, used in your app
        real_world_currency_per_point=0.05,  # Can override defaults here
        participation_fee=5.00  # Can override defaults here
    ),
]

# Default participant settings
PARTICIPANT_FIELDS = ['extraction_sum_t1']
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'

REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

INSTALLED_APPS = ['otree']  # oTree must be installed and recognized here

# Admin access
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = os.environ.get('OTREE_ADMIN_PASSWORD')  # Admin password should be set as environment variable

DEMO_PAGE_INTRO_HTML = """
Here is a demo of the CPR Bargaining Game.
"""

# Optional: Room configurations for live sessions
ROOMS = [
    dict(
        name='live_session',
        display_name='Live Bargaining Session',
        participant_label_file='_rooms/live_session.txt',  # Custom room setup if needed
    ),
]

SECRET_KEY = 'supersecretkey'  # A secret key for your project, change this to something secure
