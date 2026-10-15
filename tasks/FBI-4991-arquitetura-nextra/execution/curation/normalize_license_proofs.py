#!/usr/bin/env python3
"""Preserve API labels and add identifiers only where the exact primary text supports them."""
import datetime,hashlib,json,urllib.request
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
p=BASE/'revision-licenses.json';records=json.loads(p.read_text());sources=json.loads((BASE/'sources.json').read_text())
for key,item in records.items():
 text=(ROOT/item['artifact']).read_text(errors='replace')if item.get('artifact')and(ROOT/item['artifact']).exists()else ''
 lower=text.lower();spdx=item.get('license_spdx')
 if item.get('repo')=='eclipse-mosquitto/mosquitto' and 'SPDX-License-Identifier: EPL-2.0 OR BSD-3-Clause'in text:
  item['license_spdx']='EPL-2.0 OR BSD-3-Clause'
  item['classification_basis']='The exact root license notice explicitly declares this SPDX expression.'
 if spdx in [None,'NOASSERTION']:
  if 'redistribution and use in source and binary forms' in lower:
   item['license_spdx']='BSD-3-Clause'if('neither the name'in lower or '3. neither'in lower)else'BSD-2-Clause'
   item['classification_basis']='The exact license text contains the BSD redistribution clauses; the original API label is preserved separately.'
  elif 'gnu general public license' in lower and'version 2'in lower:
   item['license_spdx']='GPL-2.0';item['classification_basis']='The exact license text names GNU GPL version 2.'
  elif 'rabbitmq server and its tier 1' in lower and'mpl 2.0'in lower:
   item['license_spdx']='MPL-2.0';item['classification_basis']='The exact root license notice explicitly assigns MPL 2.0 to the server and core plugins.'
  elif 'elastic license 2.0'in lower:
   item['license_spdx']='Elastic-2.0';item['classification_basis']='The exact license text names Elastic License 2.0; this is not classified as an open source application license.'
  elif 'mit-only license to a dual mit/apache-2.0'in lower:
   item['license_expression']='MIT for the older contributions; MIT OR Apache-2.0 for the contributions identified by the transition notice.'
   item['classification_basis']='The root notice preserves the date and per-file conditions; no uniform identifier is invented.'

# Qt puts the licensing choice in each source header rather than a single root LICENSE.
qt=[s for s in sources.values()if s.get('repo')=='qt/qtbase'and s.get('http_status')==200 ]
for source in qt:
 key='qt/qtbase@'+source['revision'];text=(ROOT/source['artifact']).read_text();line=next(l for l in text.splitlines()if'SPDX-License-Identifier:'in l);expression=line.split('SPDX-License-Identifier:',1)[1].strip()
 records[key]={'status':'READ','repo':'qt/qtbase','revision':source['revision'],'path':source['path'],'url':source['url'].split('#')[0]+'#L1-L2','license_spdx':expression,'api_license_spdx':None,'observed_utc':source['observed_utc'],'http_status':200,'sha256':source['sha256'],'artifact':source['artifact'],'excerpt':'\n'.join(text.splitlines()[:5]),'classification_basis':'The exact source SPDX header offers the commercial license OR the stated LGPL/GPL alternatives. The selected Qt source header was read directly; each recorded source retains its own header and revision.'}

# Navigation2 declares the license at package level; preserve both package receipts.
nav=[s for s in sources.values()if s.get('repo')=='ros-navigation/navigation2'and s.get('revision')]
if nav:
 sha=nav[0]['revision'];proof=[]
 for package in ['nav2_behavior_tree','nav2_bt_navigator']:
  url=f'https://raw.githubusercontent.com/ros-navigation/navigation2/{sha}/{package}/package.xml'
  content=urllib.request.urlopen(url,timeout=20).read();text=content.decode();lines=[l.strip()for l in text.splitlines()if'<license>'in l]
  artifact=BASE/'raw'/f'navigation2-{package}-package.xml';artifact.write_bytes(content)
  proof.append({'url':f'https://github.com/ros-navigation/navigation2/blob/{sha}/{package}/package.xml','license_lines':lines,'sha256':hashlib.sha256(content).hexdigest(),'artifact':str(artifact.relative_to(ROOT)),'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')})
 records['ros-navigation/navigation2@'+sha]['package_license_proof']=proof
 expressions={line for item in proof for line in item['license_lines']}
 if all('Apache'in line and'2.0'in line for line in expressions):
  records['ros-navigation/navigation2@'+sha]['license_spdx']='Apache-2.0'
  records['ros-navigation/navigation2@'+sha]['classification_basis']='Both selected Navigation2 packages declare Apache License 2.0 in package.xml; the root mixed-license inventory is retained as the raw artifact.'
# The selected files in these historical source revisions declare Apache 2.0 directly.
for source in sources.values():
 if source.get('repo') not in ['osheroff/mysql-binlog-connector-java','debezium/debezium-server'] or source.get('http_status')!=200:continue
 key=source['repo']+'@'+source['revision']
 if records.get(key,{}).get('status')=='READ':continue
 text=(ROOT/source['artifact']).read_text();header='\n'.join(text.splitlines()[:15])
 if ('Apache License, Version 2.0'not in header and 'Apache Software License version 2.0'not in header):continue
 records[key]={'status':'READ','repo':source['repo'],'revision':source['revision'],'path':source['path'],'url':source['url'].split('#')[0]+'#L1-L15','license_spdx':'Apache-2.0','http_status':200,'observed_utc':source['observed_utc'],'artifact':source['artifact'],'sha256':source['sha256'],'excerpt':header,'classification_basis':'The exact selected source header declares Apache 2.0. This is a per-file license proof and is not used as proof of the mechanism.'}
# Some projects declare their license in source headers instead of a root LICENSE.
rare_packets=[]
for name in ['source-recommendations.json','space-based-reassessment.json','ddd-patterns-evidence.json','ddd-followon-evidence.json','transactions-source-recommendations.json']:
 path=BASE/'rare-support'/name
 if not path.exists():continue
 packet=json.loads(path.read_text())
 rare_packets.extend(packet.get('rows',packet.get('recommendations',[packet])))
for recommendation in rare_packets:
 if not recommendation.get('decision','').startswith('RECOMMEND'):continue
 application_sources=recommendation.get('application_sources',recommendation.get('application',[]))
 if not isinstance(application_sources,list):application_sources=[]
 for source in recommendation.get('base',[])+application_sources:
  proof=source.get('license',{})
  if proof.get('status') not in ['READ','READ_FILE_HEADER']:continue
  key=source['repo']+'@'+source['revision']
  if records.get(key,{}).get('status')=='READ':continue
  artifact=ROOT/proof['artifact'];content=artifact.read_bytes()
  record=dict(proof);record.update(status='READ',repo=source['repo'],revision=source['revision'],path=proof.get('path',source['path']),license_spdx=proof.get('spdx'),http_status=200,observed_utc=proof.get('observed_utc',source['observed_utc']),sha256=hashlib.sha256(content).hexdigest(),classification_basis='The exact source header or license file declares the license. This is license evidence only; the implementation mechanism is proven by separate code excerpts.')
  records[key]=record
p.write_text(json.dumps(records,ensure_ascii=False,indent=2));print('License proofs normalized from exact primary texts:',len(records))
