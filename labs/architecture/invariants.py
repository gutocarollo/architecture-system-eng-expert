"""Validate every observed field against a separately stored fixed-fixture contract."""
import json
from pathlib import Path

CONTRACT_PATH=Path(__file__).resolve().parent/'financial_contracts.json'
CONTRACTS=json.loads(CONTRACT_PATH.read_text())['probes']

def validate(probe,before,after):
    if probe not in CONTRACTS:
        raise AssertionError(f'{probe}: no reviewed invariant contract')
    expected=CONTRACTS[probe]
    if before!=expected['before']:
        raise AssertionError(f'{probe}: before violates fixture contract: {before!r}')
    if after!=expected['after']:
        raise AssertionError(f'{probe}: after violates invariant: {expected["invariant"]}; observed={after!r}')
    if probe=='deduplicate':
        assert before['debit']==250 and before['effects']==3
        assert after['debit']==150 and after['effects']==2
    if probe=='measure-signals':
        assert after['spans']==3 and after['requests']==2 and after['operations']==1
        assert after['failed_requests']==1 and after['request_error_ratio']==1/2

OBJECT_CONTRACTS=json.loads((Path(__file__).resolve().parent/'object_contracts.json').read_text())['concepts']

def validate_object(concept,before,after):
    expected=OBJECT_CONTRACTS[concept]
    assert before==expected['before'],f'{concept}: before contract violated'
    assert after==expected['after'],f'{concept}: after invariant violated: {expected["invariant"]}'
