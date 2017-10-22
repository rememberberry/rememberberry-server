import pytest
import os
import rememberberry
from rememberscript import RememberMachine
from rememberberry.testing import tmp_data_path, assert_replies, get_isolated_story
from rememberberry import ipfs

@pytest.mark.asyncio
@tmp_data_path('/tmp/data/', rm=True)
async def test_anki_account():
    storage = ipfs.get_ipfs_storage()
    storage['username'] = 'alice'
    m, storage = get_isolated_story('login_anki', storage)
    await assert_replies(m.reply(''), 'What is your Anki username?')
    await assert_replies(m.reply('ajshdkajhsdkajshd'), 'And now the password')
    await assert_replies(m.reply('jkdhskjhgdksjhg'),
                         'Authentication with ankiweb failed, try again?',
                         'What is your Anki username?')
    await assert_replies(m.reply('ankitest8080@gmail.com'), 'And now the password')
    await assert_replies(m.reply('ankitest'),
                         'Authentication worked, now I\'ll try to sync your account',
                         'Syncing anki database and media (this may take a while if you have lots of media)',
                         'Syncing done',
                         'Great, you\'re all synced up!',
                         'enter init')
