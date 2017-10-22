import os
from rememberberry.ipfs import DATA_ROOT

SCRIPTS_PATH = os.environ.get(
    'REMEMBERBERRY_SCRIPTS_PATH', os.path.join(os.path.dirname(__file__), 'scripts'))
