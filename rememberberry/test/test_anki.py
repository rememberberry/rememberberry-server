import os
import json
import shutil
import pytest
import rememberberry
from rememberscript import load_scripts_dir, validate_script
from rememberscript import RememberMachine, FileStorage
from rememberberry.auth import data_file
from rememberberry.testing import tmp_data_path, get_isolated_story, assert_replies

@pytest.mark.asyncio
@tmp_data_path('/tmp/data', delete=True)
async def test_anki():
    shutil.copytree(os.path.join(os.path.dirname(__file__), 'data'), '/tmp/data')

    username = 'asd'
    storage = FileStorage(data_file(username))
    script = load_scripts_dir(rememberberry.SCRIPTS_PATH, storage)
    validate_script(script)
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
