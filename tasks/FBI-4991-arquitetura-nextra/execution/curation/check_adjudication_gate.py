#!/usr/bin/env python3
"""Verify positive judgments and reject stale or incomplete synthetic mutations."""
import copy
import datetime
import hashlib
import json
from pathlib import Path
from adjudication_gate import adjudication_issues, carry_forward_issues, independent_decision_issues

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
load=lambda name:json.loads((BASE/name).read_text())
selections=load('source-selections.json');sources=load('sources.json');judgments=load('author-adjudications.json')
baseline={row['concept_id']:row for row in load('review-baseline.json')['concepts']}
rows={row['concept_id']:row for row in load('matrix.json')['concepts']}
closure_path=BASE.parent/'curation-repairs/independent-closure.json'
closure=json.loads(closure_path.read_text()) if closure_path.exists() else {}
decisions={row['concept_id']:row for row in closure.get('concepts',[])}
checks=[]
def require(name,condition):
 checks.append(dict(name=name,passed=bool(condition)))
 if not condition:raise AssertionError(name)
for key,judgment in judgments.items():
 require('positive:'+key,not adjudication_issues(key,selections[key],sources,judgment,ROOT))
for key,entry in baseline.items():
 if entry['carry_eligible']:
  issues=(independent_decision_issues(rows[key],decisions[key],ROOT) if key in decisions else carry_forward_issues(rows[key],entry,ROOT))
  require('preserved-first-pass:'+key,not issues)
for key in judgments:
 if key in decisions:require('actual-warm-recheck:'+key,not independent_decision_issues(rows[key],decisions[key],ROOT))
key='domain-policy';selection=selections[key];judgment=judgments[key]
def rejects(name,changed_selection=None,changed_judgment=None,changed_sources=None,kind=None):
 issues=adjudication_issues(key,changed_selection or selection,changed_sources or sources,
                          changed_judgment if changed_judgment is not None else judgment,ROOT)
 require(name,any(item['kind']==kind for item in issues) if kind else bool(issues))
rejects('missing-positive-judgment',changed_judgment={},kind='AUTHOR_ADJUDICATION_MISSING')
changed=copy.deepcopy(judgment);changed['decision']='PENDING'
rejects('pending-decision-is-not-positive',changed_judgment=changed,kind='AUTHOR_ADJUDICATION_PENDING')
changed=copy.deepcopy(judgment);changed['remaining_gates']=['The application mechanism remains unresolved.']
rejects('open-author-gate',changed_judgment=changed,kind='AUTHOR_ADJUDICATION_OPEN_GATE')
for role in ['base','application']:
 changed=copy.deepcopy(judgment);changed['primary_evidence']=[e for e in changed['primary_evidence']if e['role']!=role]
 rejects('missing-'+role+'-evidence',changed_judgment=changed,kind='AUTHOR_EVIDENCE_ROLE_MISSING')
changed=copy.deepcopy(selection);changed['limits']='The selected mechanism is explicitly still pending.'
rejects('changed-limits-invalidate-judgment',changed_selection=changed,kind='AUTHOR_ADJUDICATION_STALE')
generic=next(url for url,s in sources.items()if s.get('path','').endswith('/JpaRepository.java'))
changed=copy.deepcopy(selection);changed['base_urls']=[generic]
rejects('generic-repository-cannot-fall-back-to-positive',changed_selection=changed,kind='AUTHOR_ADJUDICATION_STALE')
changed=copy.deepcopy(judgment);changed['primary_evidence'][0]['excerpt_sha256']='0'*64
rejects('changed-excerpt',changed_judgment=changed,kind='AUTHOR_EVIDENCE_EXCERPT')
changed=copy.deepcopy(judgment);changed['primary_evidence'][0]['source_sha256']='0'*64
rejects('changed-source-binding',changed_judgment=changed,kind='AUTHOR_EVIDENCE_SOURCE_HASH')
carry_key=next(k for k,b in baseline.items()if b['carry_eligible']);changed=copy.deepcopy(rows[carry_key]);changed['base']=copy.deepcopy(rows[key]['base'])
require('changed-reviewed-source-not-carried',bool(carry_forward_issues(changed,baseline[carry_key],ROOT)))
changed=copy.deepcopy(rows[carry_key]);changed['skill']['scope']='UNADJUDICATED_GENERIC_FALLBACK'
require('changed-reviewed-skill-scope-not-carried',bool(carry_forward_issues(changed,baseline[carry_key],ROOT)))
if decisions:
 decision=copy.deepcopy(decisions[carry_key]);decision['review_sha256']='0'*64
 require('forged-review-binding-rejected',bool(independent_decision_issues(rows[carry_key],decision,ROOT)))
 changed=copy.deepcopy(rows[carry_key]);changed['mechanism']+=' Unreviewed extension.'
 require('changed-mechanism-cannot-inherit-review',bool(independent_decision_issues(changed,decisions[carry_key],ROOT)))
 changed=copy.deepcopy(rows[carry_key]);changed['base'][0]['license']['license_spdx']='UNVERIFIED'
 require('unapproved-license-change-rejected',bool(independent_decision_issues(changed,decisions[carry_key],ROOT)))
receipt=dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             scope='Deterministic current-adjudication and fingerprint checks; no semantic approval is inferred.',
             matrix_sha256=hashlib.sha256((BASE/'matrix.json').read_bytes()).hexdigest(),
             repaired_positive_judgments=len(judgments),unchanged_first_pass=sum(x['carry_eligible']for x in baseline.values()),
             checks=len(checks),failures=sum(not x['passed']for x in checks),results=checks,
             independent_pending_count=sum(row['independent_review']=='PENDING'for row in rows.values()))
(BASE/'adjudication-gate-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items()if k!='results'}))
