import os
from dotenv import load_dotenv

load_dotenv()

PROSPECT_DB = os.getenv('PROSPECT_DB', 'prospect_db')
PROSPECT_USER = os.getenv('PROSPECT_USER', 'prospect_user')
PROSPECT_PASSWORD = os.getenv('PROSPECT_PASSWORD', 'prospect_pass')
PROSPECT_DB_HOST = os.getenv('PROSPECT_DB_HOST', 'db')
PROSPECT_DB_PORT = os.getenv('PROSPECT_DB_PORT', '5432')

CONFIG_REGION_JSON = 'app/data/country-to-regions-mapping.json'
CONFIG_USER_PREFERENCES_JSON = 'app/data/users-locations-settings.json'
CONFIG_PROSPECTS_CSV = 'app/data/prospects.csv'


