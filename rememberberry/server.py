import os
import sys
import json
import asyncio
import aiohttp
import logging
import traceback
from aiohttp import web

import rememberberry
from rememberscript import RememberMachine, load_scripts_dir, validate_script
from rememberscript import FileStorage
from anki.storage import _Collection

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = web.Application()


async def cleanup(storage):
    for key, value in storage.items():
        if isinstance(value, _Collection):
            print('saving anki collection...')
            value.close(save=True)
    print('syncing storage...')
    await storage.sync()


async def message_websocket_handler(request):
    print('client connected')
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    storage = FileStorage()
    script = load_scripts_dir(rememberberry.SCRIPTS_PATH, storage)
    validate_script(script)
    machine = RememberMachine(script, storage)
    machine.init()
    try:
        async for msg in ws:
            if msg.tp == aiohttp.WSMsgType.TEXT:
                text = msg.data
                async for reply in machine.reply(text):
                    ws.send_str(reply)

            elif msg.tp == aiohttp.WSMsgType.ERROR:
                logger.info('ws connection closed with exception %s' %
                      ws.exception())
        await cleanup(storage)
    except:
        await cleanup(storage)
        traceback.print_exc()
        ws.send_str(json.dumps({'msg': traceback.format_exc()}))
        raise
    print('websocket connection closed')

    return ws


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    app.router.add_route('GET', '/messages', message_websocket_handler)
    try:
        web.run_app(app, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        asyncio.get_event_loop().run_until_complete(cleanup())
