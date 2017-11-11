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
import uuid
import shutil
import asyncio
from functools import partial
from subprocess import Popen, PIPE, STDOUT
import aiofiles
from rememberscript import FileStorage

DATA_ROOT = '/data'
# The hash of the root at DATA_ROOT folder with all the user data
# This needs to be published through IPNS whenever there's a change
DATA_ROOT_HASH = None

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
            shutil.copy('/ipfs/%s' % ipfs_hash, self.fs_path)

    async def __aexit__(self, exc_type=None, exc=None, tb=None):
        if exc is None:
            # Copy the file to mfs
            await cp_fs_to_mfs(self.fs_path, self.mfs_path, rm=True)

        # Remove the temporary file
        os.remove(self.fs_path)


class MutableFolderContext:
    """Provides a temporary mutable folder with the contents of mfs_path,
    which is then synced with ipfs when the context is exited"""
    def __init__(self, mfs_path=None):
        self.mfs_path = mfs_path

        # Get a random folder in /tmp
        self.fs_path = '/tmp/%s/' % str(uuid.uuid4())

    async def __aenter__(self):
        if self.mfs_path is not None:
            # Get the hash of mfs_path
            ipfs_folder_hash = await mfs_hash(self.mfs_path)

            if ipfs_folder_hash:
                # Copy from the readonly mount point at /ipfs/ to the tmp folder
                shutil.copytree('/ipfs/%s' % ipfs_folder_hash, self.fs_path)
            else:
                os.makedirs(self.fs_path)
        else:
            os.makedirs(self.fs_path)

    async def __aexit__(self, exc_type, exc, tb):
        if exc is None:
            # Copy the files to mfs
            await cp_fs_to_mfs(self.fs_path, self.mfs_path, rm=True, r=True)
        else:
            import traceback
            traceback.print_exception(exc_type, exc, tb)

        # Remove the temporary folder
        shutil.rmtree(self.fs_path)



def _run_commands(*commands):
    """Runs command(s) and returns their stdout and stderr
    Commands are lists of command parts"""
    results = []
    for command in commands:
        p = Popen(command, stdout=PIPE, stderr=PIPE)
        results.append(p.communicate())
    return results if len(results) > 1 else results[0]


async def _update_root_hash():
    global DATA_ROOT_HASH
    DATA_ROOT_HASH = await mfs_hash(DATA_ROOT)


async def mfs_write(mfs_path, data, mode='', update_root=True):
    assert mode in ['', 'b']
    global DATA_ROOT_HASH
    # Write to tmp file
    tmp_path = '/tmp/%s' % str(uuid.uuid4())
    async with aiofiles.open(tmp_path, 'w' + mode) as f:
        await f.write(data)

    # Add file to mfs
    await cp_fs_to_mfs(tmp_path, mfs_path, rm=True, r=True)

    # Remove tmp file
    os.remove(tmp_path)

    # Update the root
    if update_root:
        await _update_root_hash()


async def mfs_read(mfs_path, mode=''):
    assert mode in ['', 'b']

    # Get the ipfs hash
    ipfs_hash = await mfs_hash(mfs_path)
    if not ipfs_hash:
        raise FileNotFoundError()

    # Read the file from /ipfs mounting point
    async with aiofiles.open('/ipfs/%s' % ipfs_hash, 'r' + mode) as f:
        return await f.read()


async def mfs_hash(mfs_path):
    """Returns the ipfs hash if the mfs_path exists, otherwise None"""
    out, err = await asyncio.get_event_loop().run_in_executor(
        None, partial(_run_commands, ['ipfs', 'files', 'stat', mfs_path]))

    if err.decode('utf-8') != 'Error: file does not exist\n':
        lines = out.decode('utf-8').split('\n')[:-1]
        ipfs_hash, *_ = lines
        return ipfs_hash
    return None



async def mfs_mkdirs(mfs_path, update_root=True):
    global DATA_ROOT_HASH
    out, err = await asyncio.get_event_loop().run_in_executor(
        None, partial(_run_commands, ['ipfs', 'files', 'mkdir', '-p', mfs_path]))

    err = err.decode('utf-8')
    if err != '':
        print('mfs_mkdirs at %s failed: %s' % (mfs_path, err))

    if update_root:
        await _update_root_hash()


async def mfs_rm(mfs_path, r=False, update_root=True):
    global DATA_ROOT_HASH
    command = ['ipfs', 'files', 'rm', mfs_path]
    if r is True:
        command.insert(3, '-r')
    out, err = await asyncio.get_event_loop().run_in_executor(
        None, partial(_run_commands, command))

    err = err.decode('utf-8')
    if err != '':
        print('mfs_rm at %s failed: %s' % (mfs_path, err))

    if update_root:
        await _update_root_hash()


async def cp_ipfs_to_mfs(ipfs_path, mfs_path, rm=False, r=False, update_root=True):
    global DATA_ROOT_HASH
    if rm:
        await mfs_rm(mfs_path, r=r, update_root=False)

    results = await asyncio.get_event_loop().run_in_executor(
        None, partial(_run_commands, ['ipfs', 'files', 'cp', ipfs_path, mfs_path]))
    out, err = results[-1] if isinstance(results, list) else results
    e = err.decode('utf-8')

    err = err.decode('utf-8')
    if err != '':
        print('cp_ipfs_to_mfs from %s to %s failed: %s' % (ipfs_path, mfs_path, err))

    if update_root:
        await _update_root_hash()


async def cp_fs_to_mfs(fs_path, mfs_path, rm=False, r=False, update_root=True):
    args = ['ipfs', 'add', '-r', fs_path] if r else ['ipfs', 'add', fs_path]
    out, err = await asyncio.get_event_loop().run_in_executor(
        None, partial(_run_commands, args))

    err = err.decode('utf-8')
    if err != '':
        print('cp_fs_to_mfs from %s to %s failed: %s' % (fs_path, mfs_path, err))

    lines = out.decode('utf-8').split('\n')[:-1]
    _, ipfs_hash, *_ = lines[-1].split(' ')
    await cp_ipfs_to_mfs(
        '/ipfs/%s' % ipfs_hash, mfs_path, rm=rm, r=r, update_root=update_root)


async def is_daemon_running():
    out, err = await asyncio.get_event_loop().run_in_executor(
        None, partial(_run_commands, ['ipfs', 'id']))

    return err.decode('utf-8') != 'Error: api not running\n'


async def init():
    global DATA_ROOT_HASH
    if DATA_ROOT_HASH is not None:
        return

    if not await is_daemon_running():
        raise RuntimeError("IPFS daemon is not running")

    DATA_ROOT_HASH = await mfs_hash(DATA_ROOT)
    if not DATA_ROOT_HASH:
        await mfs_mkdirs(DATA_ROOT, update_root=True)


def get_ipfs_storage(filename=None):
    return FileStorage(
        filename, load_func=mfs_read, dump_func=mfs_write)
