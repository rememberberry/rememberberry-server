import os
import json
import pytest
import logging
import rememberberry
from rememberberry import ipfs
from rememberscript import load_scripts_dir, validate_script
from rememberscript import RememberMachine
from rememberberry.auth import data_file
from rememberberry.testing import tmp_data_path, assert_replies


logging.basicConfig(
    format='%(name)s %(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)


@pytest.mark.asyncio
@tmp_data_path('/tmp/data', rm=True)
async def test_study_anki():
    await ipfs.cp_fs_to_mfs(
        os.path.join(os.path.dirname(__file__), 'data'), '/tmp/data', rm=True, r=True)

    username = 'asd'
    storage = ipfs.get_ipfs_storage(data_file(username))
    script = load_scripts_dir(rememberberry.SCRIPTS_PATH, storage)
    await validate_script(script)
    await storage.load()
    m = RememberMachine(script, storage)
    m.init()

    def check_card(x):
        return x['content'].get('type', '') == 'card'

    await assert_replies(m.reply(''), 'Hey asd!', 'What would you like to do?')
    await assert_replies(m.reply('study'),
                         'Alright then, let\'s study',
                         check_card,
                         debug_print=True)
    await assert_replies(m.reply('3'),
                         'All the scheduled cards are done',
                         'What would you like to do?')


@pytest.mark.asyncio
@tmp_data_path('/tmp/data', rm=True)
async def test_decks():
    await ipfs.cp_fs_to_mfs(
        os.path.join(os.path.dirname(__file__), 'data'), '/tmp/data', rm=True, r=True)

    username = 'asd'
    storage = ipfs.get_ipfs_storage(data_file(username))
    script = load_scripts_dir(rememberberry.SCRIPTS_PATH, storage)
    await validate_script(script)
    await storage.load()
    m = RememberMachine(script, storage)
    m.init()

    def check_card(x):
        return x['content'].get('type', '') == 'card'

    await assert_replies(m.reply(''), 'Hey asd!', 'What would you like to do?')
    await assert_replies(m.reply('study'),
                         'Alright then, let\'s study',
                         check_card)
    await assert_replies(m.reply('decks'),
                         lambda x: x['replies'][0]['label'] == '1: Default [0 0 1]')
