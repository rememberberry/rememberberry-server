"""Contains various helper functions for testing conversations"""
import os
import shutil
import functools
import pytest
import rememberberry
from rememberberry import update_users_path
from rememberscript import load_scripts_dir, validate_script, load_script
from rememberscript import RememberMachine, FileStorage
from rememberscript.testing import assert_replies
from rememberscript.script import STATE_NAME, ENTER_ACTION, TRANSITIONS, TO

def tmp_data_path(data_path, delete=False):
    """This is a decorator for setting temporary paths for testing"""
    def _wrap(func):
        @functools.wraps(func)
        async def _wrapped_f(*args):
            tmp, rememberberry.DATA_PATH = rememberberry.DATA_PATH, data_path
            update_users_path()
            if delete:
                try:
                    shutil.rmtree(rememberberry.DATA_PATH)
                except:
                    pass
            await func(*args)
            rememberberry.DATA_PATH = tmp
            update_users_path()
        return _wrapped_f
    return _wrap


def get_isolated_story(name, storage):
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
    validate_script(script)
    m = RememberMachine(script, storage)
    m.init()

    return m, storage

def get_all_stories(storage):
    script = load_scripts_dir(rememberberry.SCRIPTS_PATH, storage)
    validate_script(script)
    m = RememberMachine(script, storage)
    m.init()

    return m, storage

