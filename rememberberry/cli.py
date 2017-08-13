import os
import asyncio
from rememberscript import load_scripts_dir, validate_script
from rememberscript import RememberMachine, FileStorage

async def run_loop():
    storage = FileStorage()
    path = os.path.join(os.path.dirname(__file__), 'scripts/')
    script = load_scripts_dir(path, storage)
    validate_script(script)
    machine = RememberMachine(script, storage)
    machine.init()

    try:
        while True:
            msg = input('--> ')
            async for reply in machine.reply(msg):
                print('> ', reply)
    except KeyboardInterrupt:
        print('syncing storage')
        await storage.sync()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run_loop())
