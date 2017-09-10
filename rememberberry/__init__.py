import os

SCRIPTS_PATH = os.environ.get('REMEMBERBERRY_SCRIPTS_PATH',
                              os.path.join(os.path.dirname(__file__), 'scripts'))
DATA_PATH = os.environ.get('REMEMBERBERRY_DATA_PATH',
                           os.path.join(os.path.dirname(__file__), 'data'))
USERS_PATH = None
def update_users_path():
    global USERS_PATH
    USERS_PATH = os.path.join(DATA_PATH, 'users')

update_users_path()
