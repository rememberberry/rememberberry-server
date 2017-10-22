import json
import pytest
import rememberberry
from rememberscript import load_scripts_dir, validate_script, load_script
from rememberberry import ipfs
from rememberberry.testing import (tmp_data_path, assert_replies,
                                   get_isolated_story, get_all_stories)


@pytest.mark.asyncio
@tmp_data_path('/tmp/data/', rm=True)
async def test_signup_login():
    # Test sign up
    auth_token = lambda x: 'auth_token=' in x['content']
    storage = ipfs.get_ipfs_storage()
    storage['name'] = 'benny'
    m, storage = get_isolated_story('sign_up', storage)
    await assert_replies(m.reply(''), 'What username would you like to have?')
    await assert_replies(m.reply('benny'), 'What password would you like?')
    await assert_replies(m.reply('asd'),
                         'The password is too short, we recommend > 6 characters',
                         'Please try again',
                         'What password would you like?')
    await assert_replies(m.reply('asdasd'),
                         'Now type the password again so we know there\'s no typo in there')
    await assert_replies(m.reply('asdasd2'),
                         'Sorry, that didn\'t match what you typed before, let\'s start over',
                         'What password would you like?')
    await assert_replies(m.reply('asdasd'),
                         'Now type the password again so we know there\'s no typo in there')
    await assert_replies(m.reply('asdasd'),
                         auth_token,
                         'Great, we\'re all done!',
                         'enter init')
    storage['initial_setup_done'] = True
    await storage.sync()

    # Test login
    assert storage.get('username', None) == 'benny'

    storage = ipfs.get_ipfs_storage()
    m, storage = get_isolated_story('login', storage)
    await assert_replies(m.reply(''), 'What is your username?')
    await assert_replies(m.reply('benny2'), 'And now the password')
    await assert_replies(m.reply('asdasd'),
                         'There is no account with that username + password combo, please try again',
                         'What is your username?')
    await assert_replies(m.reply('benny'), 'And now the password')
    await assert_replies(m.reply('asdasd'), 
                         "Great, you're all logged in!",
                         auth_token,
                         'enter init')

    assert storage.get('username', None) == 'benny'

    auth_token = storage['auth_token']

    # Test auth
    storage = ipfs.get_ipfs_storage()
    m, storage = get_all_stories(storage)
    await assert_replies(m.reply('auth_token=%s' % auth_token),
                         'Hey benny!',
                         'What would you like to do?')
