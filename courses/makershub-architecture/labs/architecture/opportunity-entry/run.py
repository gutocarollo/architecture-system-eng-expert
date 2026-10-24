"""Execute real function bodies with explicit, network-free adapter doubles."""
import ast
import asyncio
import logging
import os
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parent

def functions(source, names, namespace):
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in names]
    missing = set(names) - {node.name for node in nodes}
    if missing:
        raise RuntimeError(f'source functions missing: {missing}')
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *nodes], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), '<immutable historical AST slice>', 'exec'), namespace)

def booking(phase):
    created = []
    def create(payload):
        created.append(payload)
        return {'success': True, 'id': '006SYNTHETICNEW1'}
    sf = SimpleNamespace(Opportunity=SimpleNamespace(create=create), sf_instance='local-double')
    def post_steps(**kwargs):
        kwargs['steps_completed'].extend(['event_created', 'opportunity_updated'])
    namespace = dict(os=os, logger=logging.getLogger('lab'), date=date, datetime=datetime,
        timedelta=timedelta, MEETING_DURATION=30, get_salesforce_connection=lambda: sf,
        resolve_write_connection=lambda *_: sf, _validate_sf_id=lambda value: value,
        _execute_post_opportunity_steps=post_steps, R1_CRITICAL_STEPS={'event_created', 'opportunity_updated'},
        is_sf_user_access_error=lambda _: False)
    source = (ROOT / f'{phase}-integration.py').read_text()
    functions(source, {'execute_r1_from_opportunity_flow'}, namespace)
    result = namespace['execute_r1_from_opportunity_flow'](
        source_opp_id='006SYNTHETICOPEN', account_id='001SYNTHETICACC1', contact_id=None,
        client_name='Synthetic client', patrimony_value=1000, patrimony_range='local', profissao='synthetic',
        interesse_investimentos='synthetic', description='isolated lab', event_datetime=datetime(2026,10,14),
        advisor_salesforce_id='005SYNTHETICADV1', advisor_name='Synthetic advisor',
        sdr_salesforce_id='005SYNTHETICSDR1', sdr_name='Synthetic operator')
    print(f'{phase}: create_calls={len(created)} opportunity_id={result["opportunity_id"]} downstream=double')
    assert (len(created), result['opportunity_id']) == ((1, '006SYNTHETICNEW1') if phase == 'before' else (0, '006SYNTHETICOPEN'))

class LabHttpException(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail

async def claims():
    held = set()
    async def claim(scope, actor, key):
        identity = (scope, actor, key)
        if identity in held:
            return SimpleNamespace(outcome='BUSY', owner_token=None)
        held.add(identity)
        return SimpleNamespace(outcome='OWN', owner_token='synthetic-token')
    store = SimpleNamespace(claim_or_replay=claim, OWN='OWN')
    first = await claim('qualify', 'operator-a', 'key-a')
    second = await claim('qualify', 'operator-b', 'key-b')
    print(f'before-claim: two_actor_keys_own={int(first.outcome=="OWN")+int(second.outcome=="OWN")}')
    async def heartbeat(*args, **kwargs):
        await asyncio.Event().wait()
    namespace = dict(asyncio=asyncio, idempotency_store=store, logger=logging.getLogger('lab'),
        _OPPORTUNITY_ENTRY_IDEMPOTENCY_SCOPE='super_r1_opportunity_entry',
        _OPPORTUNITY_ENTRY_IDEMPOTENCY_ACTOR='system@super-r1-opportunity-entry',
        _idempotency_heartbeat=heartbeat, HTTPException=LabHttpException,
        status=SimpleNamespace(HTTP_409_CONFLICT=409))
    functions((ROOT/'after-qualify.py').read_text(), {'_claim_opportunity_entry'}, namespace)
    _, task = await namespace['_claim_opportunity_entry']('006SYNTHETICOPEN')
    try:
        await namespace['_claim_opportunity_entry']('006SYNTHETICOPEN')
        raise AssertionError('second actor should be refused')
    except LabHttpException as error:
        print(f'after-claim: shared_opportunity_second_status={error.status_code}')
        assert error.status_code == 409
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

def refusal():
    namespace = dict(Enum=Enum, date=date, SUPER_R1_OPPORTUNITY_RECORD_TYPES={'Investimentos', 'FS'}, _STAND_BY_LOSS_REASON='Stand By')
    functions((ROOT/'after.py').read_text(), {'record_type_developer_name', '_lost_opportunity_refusal', 'lost_opportunity_refusal', 'opportunity_entry_refusal'}, namespace)
    for state, won, expected in [('Contatado', False, 0), ('Ganha', True, 409), ('Perdida', False, 409)]:
        result = namespace['opportunity_entry_refusal']({'Id':'006SYNTHETICOPEN','AccountId':'001SYNTHETICACC1','StageName':state,'IsWon':won})
        status = result[0] if result else 0
        print(f'after-policy: stage={state} status={status}')
        assert status == expected

for phase in ['before', 'after']:
    booking(phase)
asyncio.run(claims())
refusal()
print('comparison=PASS scope=historical_function_bodies_with_adapter_doubles')
