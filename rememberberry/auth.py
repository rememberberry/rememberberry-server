import os
import hashlib
from secrets import token_hex
import aiofiles
import rememberberry

# Store auth tokens -> (username, password) map in memory for login with tokens
ACTIVE_AUTH_TOKENS = {}

def account_hex(username):
    return hashlib.sha256(bytes(username, 'utf-8')).hexdigest()


def account_password_hex(username, password):
    return hashlib.sha256(bytes(username+password, 'utf-8')).hexdigest()


def data_file(username):
    file_path = '%s/data.pickle' % account_hex(username)
    return os.path.join(rememberberry.USERS_PATH, file_path)


def auth_file(username, password):
    file_path = '%s/%s.auth' % (account_hex(username),
                                account_password_hex(username, password))
    return os.path.join(rememberberry.USERS_PATH, file_path)


async def login(username, password, storage):
    # NOTE: os.path.exists is blocking io
    if (not os.path.exists(data_file(username)) or
        not os.path.exists(auth_file(username, password))):
        return False

    storage.filename = data_file(username)
    await storage.load()
    return True


async def login_with_token(auth_token, storage):
    print('logging in with token %s' % auth_token)
    if auth_token not in ACTIVE_AUTH_TOKENS:
        print('token not active')
        return False
    return await login(*ACTIVE_AUTH_TOKENS[auth_token], storage)


async def create_account(username, password, storage):
    os.makedirs(os.path.dirname(data_file(username))) # NOTE: blocking io
    async with aiofiles.open(auth_file(username, password), 'w') as f:
        f.write(username)

    storage.filename = data_file(username)
    await storage.sync()


def generate_auth_token(username, password):
    token = token_hex(16)
    ACTIVE_AUTH_TOKENS[token] = (username, password)
    return token


def validate_username(username):
    if len(username) == 0:
        return False, "The username has to contain, you know... something"
    # NOTE: os.path.exists is blocking io
    if os.path.exists(data_file(username)):
        return False, "Sorry, that username is taken by someone else"
    return True, None


def validate_password(password):
    if len(password) < 6:
        return False, "The password is too short, we recommend > 6 characters"
    return True, None
