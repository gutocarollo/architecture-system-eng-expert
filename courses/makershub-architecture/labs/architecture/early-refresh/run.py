"""Use a controlled clock without patching the event loop's clock."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent

async def exercise(phase):
    spec = importlib.util.spec_from_file_location(phase, ROOT / f'{phase}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    now = [0.0]
    module.time = SimpleNamespace(monotonic=lambda: now[0])
    calls = 0
    started, release = asyncio.Event(), asyncio.Event()
    async def producer():
        nonlocal calls
        calls += 1
        if calls == 1:
            return 'calls-v1'
        started.set()
        await release.wait()
        return 'calls-v2'
    settings = {'ttl_seconds': 1.0}
    if phase == 'after':
        settings['early_ttl_seconds'] = 0.5
    cache = module.SingleFlightCache(**settings)
    assert await cache.get(producer) == 'calls-v1'
    await asyncio.sleep(0)
    now[0] = 0.6
    assert await cache.get(producer) == 'calls-v1'
    await asyncio.sleep(0)
    early_started = started.is_set()
    if early_started:
        release.set()
        await cache._inflight
        await asyncio.sleep(0)
    now[0] = 1.05
    boundary = asyncio.create_task(cache.get(producer))
    for _ in range(3):
        await asyncio.sleep(0)
    blocked = not boundary.done()
    release.set()
    result = await boundary
    print(f'{phase}: early_started={early_started} boundary_blocked={blocked} result={result} producer_calls={calls}')
    assert (early_started, blocked, result, calls) == ((False, True, 'calls-v2', 2) if phase == 'before' else (True, False, 'calls-v2', 2))

async def main():
    for phase in ['before', 'after']:
        await exercise(phase)
    print('comparison=PASS evolution=True slow_refresh_can_still_block_after_hard_ttl=True')

asyncio.run(main())
