import os
import json
import asyncio
import traceback
from string import Template
from functools import partial
import anki
import anki.storage
from anki.storage import Collection
from anki.sched import Scheduler
from anki.sync import FullSyncer, RemoteServer, MediaSyncer, RemoteMediaServer
import rememberberry
from rememberberry.auth import account_hex

PROGRESS_TMPL = Template(
"""<div>
    <span style="color: blue; ${blue_ul}">${blue}</span>
    <span style="color: green; ${green_ul}">${green}</span>
    <span style="color: red; ${red_ul}">${red}</span>
</div>""")

def _get_hkey(anki_username, anki_password):
    return RemoteServer(None).hostKey(anki_username, anki_password)


async def get_anki_hkey(anki_username, anki_password):
     return await asyncio.get_event_loop().run_in_executor(
            None, partial(_get_hkey, anki_username, anki_password))


def get_user_dir(username):
    return os.path.join(rememberberry.USERS_PATH, '%s' % account_hex(username))

def anki_col_path(username):
    return os.path.join(get_user_dir(username), 'collection.anki2')

def get_anki_col(username):
    try:
        os.makedirs(get_user_dir(username)) # NOTE: blocking io
    except:
        pass
    return Collection(anki_col_path(username))


async def initial_anki_sync(username, anki_hkey, storage):
    """Downloads a users's anki database and media files to rememberberry"""
    try:
        col = get_anki_col(username)

        yield 'Syncing anki database'

        server = RemoteServer(anki_hkey)
        client = FullSyncer(col, anki_hkey, server.client)
        client.download()
        col = get_anki_col(username) # reload collection

        yield 'Syncing media files (this may take a while)'

        media_server = RemoteMediaServer(col, anki_hkey, server.client)
        media_client = MediaSyncer(col, media_server)
        media_client.sync()
        col.close(save=True)
    except:
        storage['anki_sync_successful'] = False
        storage['anki_error_msg'] = traceback.format_exc()
        print(storage['anki_error_msg'])
        try:
            os.remove(anki_col_path(username)) # NOTE: blocking io
        except:
            pass
        yield 'Something went wrong...'
        return

    yield 'Syncing done'
    storage['anki_sync_successful'] = True


def _remaining_counts(scheduler, card):
    if not scheduler.col.conf['dueCounts']:
        return None, None
    counts = list(scheduler.counts(card))
    idx = scheduler.countIdx(card)
    return counts, idx


def _answer_button_list(scheduler, card):
    l = [(1, "Again")]
    cnt = scheduler.answerButtons(card)
    if cnt == 2:
        return l + [(2, "Good")]
    elif cnt == 3:
        return l + [(2, "Good"), (3, "Easy")]
    else:
        return l + [(2, "Hard"), (3, "Good"), (4, "Easy")]


def _get_timing(scheduler, card, ease):
    if not scheduler.col.conf['estTimes']:
        return ''
    return scheduler.nextIvlStr(card, ease, True)


def format_anki_question(scheduler, card, storage):
    question = card.q()
    num_answer_buttons = scheduler.answerButtons(card)
    storage['_num_answer_buttons'] = num_answer_buttons
    buttons = []
    color_map = {
        'Again': 'red',
        'Hard': 'lightyellow',
        'Good': 'lightblue',
        'Easy': 'lightgreen',
    }
    for ease, label in _answer_button_list(scheduler, card):
        timing = _get_timing(scheduler, card, ease)
        buttons.append({
            'msg': ease,
            'label': '%s (%s)' % (label, timing),
            'color': color_map[label]
        })

    counts, idx = _remaining_counts(scheduler, card)
    def prepend_progress(html):
        ulstr = "text-decoration: underline"
        return (PROGRESS_TMPL.substitute(
            blue=counts[0], red=counts[1], green=counts[2],
            blue_ul=(ulstr if idx == 0 else ''),
            red_ul=(ulstr if idx == 1 else ''),
            green_ul=(ulstr if idx == 2 else '')) + html)
    return {
        'content': {
            'type': 'card',
            'front': prepend_progress(card.q()),
            'back': prepend_progress(card.a())
        },
        'replies': buttons
    }


def answer_card(scheduler, card, msg):
    ease = int(msg)
    scheduler.answerCard(card, ease=ease)
