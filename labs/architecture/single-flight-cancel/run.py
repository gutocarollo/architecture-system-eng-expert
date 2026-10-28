"""Run the same cancellation against both immutable MakersHub modules."""
import asyncio
import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load(phase, candidate=None):
    spec = importlib.util.spec_from_file_location(phase, candidate or ROOT / f'{phase}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

async def exercise(phase, candidate=None):
    module = load(phase, candidate)
    calls = 0
    started, release = asyncio.Event(), asyncio.Event()
    async def producer():
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return 'synthetic-online-call'
    cache = module.SingleFlightCache(ttl_seconds=1)
    readers = [asyncio.create_task(cache.get(producer)) for _ in range(5)]
    await started.wait()
    await asyncio.sleep(0)
    readers[0].cancel()
    await asyncio.sleep(0)
    release.set()
    results = await asyncio.gather(*readers, return_exceptions=True)
    cancelled = sum(isinstance(x, asyncio.CancelledError) for x in results)
    survivors = sum(x == 'synthetic-online-call' for x in results)
    print(f'{phase}: readers=5 cancelled={cancelled} survivors={survivors} producer_calls={calls}')
    assert (cancelled, survivors, calls) == ((5, 0, 1) if phase == 'before' else (1, 4, 1))

async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path)
    args=parser.parse_args()
    if args.candidate:
        await exercise('candidate', args.candidate)
        print('candidate=PASS surviving_readers=4')
    else:
        for phase in ['before', 'after']:
            await exercise(phase)
        print('comparison=PASS before_defect_observed=True after_guarantee_observed=True')

asyncio.run(main())
