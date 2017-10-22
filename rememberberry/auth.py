import os
import hashlib
from secrets import token_hex
import aiofiles
import rememberberry
from rememberberry import ipfs

# Store auth tokens -> (username, password) map in memory for login with tokens
ACTIVE_AUTH_TOKENS = {}

def account_hex(username):
    return hashlib.sha256(bytes(username, 'utf-8')).hexdigest()


def account_password_hex(username, password):
    return hashlib.sha256(bytes(username+password, 'utf-8')).hexdigest()


def data_file(username):
    file_path = '%s/data.pickle' % account_hex(username)
    return os.path.join(ipfs.DATA_ROOT, 'users', file_path)


def auth_file(username, password):
    file_path = '%s/%s.auth' % (account_hex(username),
                                account_password_hex(username, password))
    return os.path.join(ipfs.DATA_ROOT, 'users', file_path)


async def login(username, password, storage):
    if (not await ipfs.mfs_hash(data_file(username)) or
        not await ipfs.mfs_hash(auth_file(username, password))):
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
    await ipfs.mfs_mkdirs(os.path.dirname(data_file(username))) # NOTE: blocking io

    await ipfs.mfs_write(auth_file(username, password), username)

    storage.filename = data_file(username)
    await storage.sync()


def generate_auth_token(username, password):
    token = token_hex(16)
    ACTIVE_AUTH_TOKENS[token] = (username, password)
    return token


async def validate_username(username):
    if len(username) == 0:
        return "The username has to contain, you know... something"
    if await ipfs.mfs_hash(data_file(username)):
        return "Sorry, that username is taken by someone else"
    return None


def validate_password(password):
    if len(password) < 6:
        return "The password is too short, we recommend > 6 characters"
    return None
