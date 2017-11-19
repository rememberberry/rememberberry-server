"""Contains various helper functions for testing conversations"""
import os
import functools
import pytest
import rememberberry
from rememberberry import ipfs
from rememberscript import load_scripts_dir, validate_script, load_script
from rememberscript import RememberMachine
from rememberscript.testing import assert_replies
from rememberscript.script import STATE_NAME, ENTER_ACTION, TRANSITIONS, TO

def tmp_data_path(data_path, rm=False):
    """This is a decorator for setting temporary paths for testing"""
    def _wrap(func):
        @functools.wraps(func)
        async def _wrapped_f(*args):
            await ipfs.init()
            tmp, rememberberry.ipfs.DATA_ROOT = rememberberry.ipfs.DATA_ROOT, data_path
            if rm:
                try:
                    await ipfs.mfs_rm(rememberberry.ipfs.DATA_ROOT, r=True)
                except:
                    pass
            await func(*args)
            rememberberry.ipfs.DATA_ROOT = tmp
        return _wrapped_f
    return _wrap


async def get_isolated_story(name, storage):
    name_script = load_script(rememberberry.SCRIPTS_PATH, name, storage)
    script = {name: name_script}
    script['init'] = [
        {
            STATE_NAME: 'init',
            ENTER_ACTION: 'enter init',
            TRANSITIONS: {
                TO: name
            }
        }
    ]
    await validate_script(script)
    m = RememberMachine(script, storage)
    m.init()

    return m, storage

async def get_all_stories(storage):
    script = load_scripts_dir(rememberberry.SCRIPTS_PATH, storage)
    await validate_script(script)
    m = RememberMachine(script, storage)
    m.init()

    return m, storage

