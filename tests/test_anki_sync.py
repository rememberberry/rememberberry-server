import pytest
import os
import rememberberry
from rememberscript import RememberMachine, FileStorage
from rememberberry.testing import tmp_data_path, assert_replies, get_isolated_story

@pytest.mark.asyncio
@tmp_data_path('/tmp/data/', delete=True)
async def test_anki_account():
    storage = FileStorage()
    m, storage = get_isolated_story('login_anki', storage)
    await assert_replies(m.reply(''), 'What is your Anki username?')
    await assert_replies(m.reply('ajshdkajhsdkajshd'), 'And now the password')
    await assert_replies(m.reply('jkdhskjhgdksjhg'),
                         'Authentication with ankiweb failed, try again?',
                         'What is your Anki username?')
    await assert_replies(m.reply('ankitest8080@gmail.com'), 'And now the password')
    await assert_replies(m.reply('ankitest'),
                         'Authentication worked, now I\'ll try to sync your account',
                         'Syncing anki database',
                         'Syncing media files (this may take a while)',
                         'Syncing done',
                         'Great, you\'re all synced up!',
                         'enter init')
