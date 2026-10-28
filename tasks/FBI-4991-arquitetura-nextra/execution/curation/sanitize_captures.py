#!/usr/bin/env python3
"""Publish sanitized public captures while retaining original source hashes."""
import datetime,hashlib,html,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
receipts=[]
source_file=BASE/'raw/b2d0e2b9ab419f00583f994129f7acc65e369e87927326b673e032084d7284b5.txt'
source_index=BASE/'sources.json';sources=json.loads(source_index.read_text())
if source_file.exists():
 original=source_file.read_bytes();lines=original.decode().splitlines(keepends=True);changed=[]
 for number in [656,1876]:
  line=lines[number-1]
  redacted=re.sub(r'(?i)([x-]*api[-_]?key\s*:\s*)[^\"\'\r\n]+',r'\1REDACTED',line)
  if redacted==line and 'REDACTED' not in line:
   # Only the flagged command is replaced; no credential is printed or retained elsewhere.
   redacted='curl [authorization example redacted from the upstream documentation]\n'
  if redacted!=line:changed.append(number);lines[number-1]=redacted
 sanitized=''.join(lines).encode();source_file.write_bytes(sanitized)
 source_keys=[]
 for key,record in sources.items():
  if record.get('artifact','').endswith(source_file.name):
   record.setdefault('original_artifact_sha256',record.get('remote_sha256',record['sha256']))
   record.setdefault('remote_sha256',record['original_artifact_sha256'])
   record['artifact_sha256']=hashlib.sha256(sanitized).hexdigest()
   record['sha256']=record['artifact_sha256']
   record['artifact_sanitization']='Public upstream APISIX documentation authorization examples redacted; the original remote-source hash is retained in remote_sha256 and original_artifact_sha256.'
   source_keys.append(key)
 receipts.append({'artifact':str(source_file),'classification':'PUBLIC_UPSTREAM_DOCUMENTATION_AUTHORIZATION_EXAMPLES','original_sha256':next((sources[k]['original_artifact_sha256']for k in source_keys),hashlib.sha256(original).hexdigest()),'sanitized_sha256':hashlib.sha256(sanitized).hexdigest(),'redacted_lines':changed,'source_urls':source_keys,'observed_utc':now()})
source_index.write_text(json.dumps(sources,ensure_ascii=False,indent=2))

capture=BASE/'github-trending-monthly-2026-10-15.html'
trend_file=BASE/'trending-monthly.json';trend=json.loads(trend_file.read_text())
text=capture.read_text()
if 'sanitized-visible-repository-cards' not in text:
 articles=re.findall(r'<article\b.*?</article>',text,re.S);blocks=[]
 for article in articles:
  heading=re.search(r'<h2.*?</h2>',article,re.S)
  title=''.join(re.sub('<[^>]+>',' ',heading.group(0)).split())if heading else ''
  visible=html.unescape(re.sub('<[^>]+>',' ',article));visible=' '.join(visible.split())
  blocks.append('<article><h2>'+html.escape(title)+'</h2><p>'+html.escape(visible)+'</p></article>')
 safe='<!doctype html>\n<html><head><meta charset="utf-8"><title>GitHub Trending monthly: sanitized visible repository cards</title></head><body>\n<!-- sanitized-visible-repository-cards; scripts, session/CSRF attributes and hidden payloads omitted -->\n'+'\n'.join(blocks)+'\n</body></html>\n'
 capture.write_text(safe)
trend['artifact_sha256']=hashlib.sha256(capture.read_bytes()).hexdigest()
trend['artifact_sanitization']='Visible repository card text retained; scripts, hidden payloads and session/CSRF attributes removed. raw_sha256 preserves the original HTTP response hash.'
trend_file.write_text(json.dumps(trend,ensure_ascii=False,indent=2))
receipts.append({'artifact':str(capture),'classification':'PUBLIC_UNAUTHENTICATED_GITHUB_PAGE_HIDDEN_SESSION_DATA','original_sha256':trend['raw_sha256'],'sanitized_sha256':trend['artifact_sha256'],'retained_repository_cards':len(trend['rows']),'observed_utc':now()})
(BASE/'sanitization-receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2))
print(json.dumps({'captures':len(receipts),'secret_values_printed':False,'source_hashes_preserved':True}))
