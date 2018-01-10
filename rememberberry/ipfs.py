"""
Helper functions that abstract away modifying files in the IPFS store

This module keeps track of the data root hash and updates it whenever
any data in it updates, and in a separate thread continuously publishes
the new ipns link

Note that paths are referred to by the prefixes:
'fs': normal file system
'mfs': mutable ipfs paths
'ipfs': immutable ipfs paths
"""
import os
import io
import uuid
import shutil
import asyncio
import logging
from functools import partial
from subprocess import Popen, PIPE, STDOUT
import aiofiles
from rememberscript import FileStorage
from rememberberry import ipfsapi_asyncio

DATA_ROOT = '/data'
# The hash of the root at DATA_ROOT folder with all the user data
# This needs to be published through IPNS whenever there's a change
DATA_ROOT_HASH = None
API = None # ipfs api

class MutableFileContext:
    """Provides a temporary file with the contents of mfs_path,
    which is then synced with ipfs when the context is exited"""
    def __init__(self, ext=None, mfs_path=None):
        self.mfs_path = mfs_path

        # Get a random file in /tmp
        if ext:
            self.fs_path = '/tmp/%s.%s' % (str(uuid.uuid4()), ext)
        else:
            self.fs_path = '/tmp/%s' % str(uuid.uuid4())


    async def __aenter__(self):
        if self.mfs_path is not None:
            # Get the hash of mfs_path
            ipfs_hash = await mfs_hash(self.mfs_path)

            # Copy from the readonly mount point at /ipfs/ to the tmp file
            _cp = partial(shutil.copy, '/ipfs/%s' % ipfs_hash, self.fs_path)
            await asyncio.get_event_loop().run_in_executor(None, _cp)

    async def __aexit__(self, exc_type=None, exc=None, tb=None):
        if exc is None:
            # Copy the file to mfs
            await cp_fs_to_mfs(self.fs_path, self.mfs_path, rm=True)

        # Remove the temporary file
        _rm = partial(os.remove, self.fs_path)
        await asyncio.get_event_loop().run_in_executor(None, _rm)


class MutableFolderContext:
    """Provides a temporary mutable folder with the contents of mfs_path,
    which is then synced with ipfs when the context is exited"""
    def __init__(self, mfs_path=None):
        self.mfs_path = mfs_path

        # Get a random folder in /tmp
        self.fs_path = '/tmp/%s/' % str(uuid.uuid4())

    async def __aenter__(self):
        _mkdirs = partial(os.makedirs, self.fs_path)
        if self.mfs_path is not None:
            # Get the hash of mfs_path
            ipfs_folder_hash = await mfs_hash(self.mfs_path)

            if ipfs_folder_hash:
                # Copy from the readonly mount point at /ipfs/ to the tmp folder
                _cp = partial(shutil.copytree, '/ipfs/%s' % ipfs_folder_hash, self.fs_path)
                await asyncio.get_event_loop().run_in_executor(None, _cp)
            else:
                await asyncio.get_event_loop().run_in_executor(None, _mkdirs)
        else:
            await asyncio.get_event_loop().run_in_executor(None, _mkdirs)

    async def __aexit__(self, exc_type, exc, tb):
        if exc is None:
            # Copy the files to mfs
            logging.debug('exiting folder context')
            await cp_fs_to_mfs(self.fs_path, self.mfs_path, rm=True, r=True)
        else:
            import traceback
            traceback.print_exception(exc_type, exc, tb)

        # Remove the temporary folder
        _rmtree = partial(shutil.rmtree, self.fs_path)
        await asyncio.get_event_loop().run_in_executor(None, _rmtree)


async def _update_root_hash():
    global DATA_ROOT_HASH
    DATA_ROOT_HASH = await mfs_hash(DATA_ROOT)


async def mfs_write(mfs_path, data, mode='', update_root=True):
    assert mode in ['', 'b']
    global DATA_ROOT_HASH
    data = bytes(data, 'utf-8') if mode == '' else data
    try:
        await API.files_write(mfs_path, io.BytesIO(data), create=True)
    except:
        logging.info('mfs_write failed with path %s' % mfs_path)
        raise

    # Update the root
    if update_root:
        await _update_root_hash()


async def mfs_read(mfs_path, mode=''):
    assert mode in ['', 'b']

    try:
        ret = await API.files_read(mfs_path)
    except:
        raise FileNotFoundError()

    if mode == 'b':
        return ret
    else:
        return str(ret, 'utf-8')


async def mfs_hash(mfs_path):
    """Returns the ipfs hash if the mfs_path exists, otherwise None"""
    try:
        ret = await API.files_stat(mfs_path)
        logging.debug('_files_stat returning %s' % str(ret))
    except:
        return None

    return ret['Hash']


async def mfs_mkdirs(mfs_path, update_root=True):
    global DATA_ROOT_HASH
    try:
        await API.files_mkdir(mfs_path, parents=True)
    except:
        logging.debug('mfs_mkdirs at %s failed' % mfs_path)
        return None

    if update_root:
        await _update_root_hash()


async def mfs_rm(mfs_path, r=False, update_root=True):
    global DATA_ROOT_HASH

    try:
        await API.files_rm(mfs_path, recursive=r)
    except:
        logging.info('mfs_rm at %s failed' % mfs_path)
        return None

    if update_root:
        await _update_root_hash()


async def cp_ipfs_to_mfs(ipfs_path, mfs_path, rm=False, r=False, update_root=True):
    global DATA_ROOT_HASH
    if rm:
        await mfs_rm(mfs_path, r=r, update_root=False)

    try:
        await API.files_cp(ipfs_path, mfs_path)
    except:
        logging.info('cp_ipfs_to_mfs from %s to %s failed' % (ipfs_path, mfs_path))
        return None

    if update_root:
        await _update_root_hash()


async def add_files_ipfsapi(fs_path, r=False):
    try:
        ret = await API.add(fs_path, recursive=r)
    except:
        logging.info('add_files_ipfsapi at %s failed' % fs_path)
        return None

    last = ret[-1] if isinstance(ret, list) else ret
    ipfs_hash = last['Hash']
    return ipfs_hash


def _run_commands(*commands):
    """Runs command(s) and returns their stdout and stderr
    Commands are lists of command parts"""
    results = []
    for command in commands:
        p = Popen(command, stdout=PIPE, stderr=PIPE)
        results.append(p.communicate())
    return results if len(results) > 1 else results[0]


async def add_files_goipfs(fs_path, r=False):
    # -Q flag to force only final hash output
    args = ['ipfs', 'add', '-r', '-Q', fs_path] if r else ['ipfs', 'add', '-Q', fs_path]
    out, err = await asyncio.get_event_loop().run_in_executor(
        None, partial(_run_commands, args))

    err = err.decode('utf-8')
    if err != '':
        logging.info('add_files_goipfs at %s failed: %s' % (fs_path, err))
        raise RuntimeError

    return out.decode('utf-8').strip()


async def cp_fs_to_mfs(fs_path, mfs_path, rm=False, r=False, update_root=True):
    # Use goipfs for now, since ipfsapi runs out of memory when adding
    # big folders: https://github.com/ipfs/py-ipfs-api/issues/104
    #ipfs_hash = await add_files_ipfsapi(fs_path, r=r)
    ipfs_hash = await add_files_goipfs(fs_path, r=r)

    await cp_ipfs_to_mfs(
        '/ipfs/%s' % ipfs_hash, mfs_path, rm=rm, r=r, update_root=update_root)


async def init():
    global DATA_ROOT_HASH, API
    if DATA_ROOT_HASH is not None:
        return

    try:
        API = await ipfsapi_asyncio.connect()
    except:
        logging.critical("Couldn't connect to ipfs, is it running?")
        raise

    DATA_ROOT_HASH = await mfs_hash(DATA_ROOT)
    if not DATA_ROOT_HASH:
        await mfs_mkdirs(DATA_ROOT, update_root=True)


def get_ipfs_storage(filename=None):
    return FileStorage(
        filename, load_func=mfs_read, dump_func=mfs_write)
