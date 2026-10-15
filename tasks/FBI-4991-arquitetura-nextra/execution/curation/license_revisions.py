#!/usr/bin/env python3
"""Read license files at the exact revisions used by the curation."""
import concurrent.futures,datetime,hashlib,json,subprocess,urllib.request
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
source=json.loads((BASE/'sources.json').read_text())
selections=json.loads((BASE/'source-selections.json').read_text())
skills=json.loads((BASE/'skill-candidates.json').read_text())
urls={u for item in selections.values() for key in ['base_urls','application_urls'] for u in item[key]}
urls.update(v['url'] for v in skills.values())
targets={(source[u]['repo'],source[u]['revision']) for u in urls if source.get(u,{}).get('revision') and (source[u].get('http_status')==200 or source[u].get('kind')=='REPOSITORY_OR_DIRECTORY')}
output=BASE/'revision-licenses.json'
existing=json.loads(output.read_text()) if output.exists() else {}
def collect(target):
 repo,sha=target; key=repo+'@'+sha
 if key in existing:return key,existing[key]
 p=subprocess.run(['gh','api',f'repos/{repo}/license?ref={sha}'],capture_output=True,text=True)
 now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
 if p.returncode:return key,{'status':'UNRESOLVED','repo':repo,'revision':sha,'error':p.stderr[:250],'observed_utc':now}
 d=json.loads(p.stdout)
 import base64
 content=base64.b64decode(d.get('content','')); text=content.decode(errors='replace')
 artifact=BASE/'raw'/('license-'+hashlib.sha256(key.encode()).hexdigest()+'.txt');artifact.write_bytes(content)
 spdx=(d.get('license') or {}).get('spdx_id')
 if not spdx or spdx=='NOASSERTION':
  if 'Permission to use, copy, modify, and distribute this software' in text:spdx='PostgreSQL'
  elif 'Mozilla Public License' in text and ('2.0' in text or 'Version 2' in text):spdx='MPL-2.0'
  elif 'Apache License' in text and '2.0' in text:spdx='Apache-2.0'
  elif 'GNU GENERAL PUBLIC LICENSE' in text and 'Version 2' in text:spdx='GPL-2.0'
  elif 'GNU GENERAL PUBLIC LICENSE' in text and 'Version 3' in text:spdx='GPL-3.0'
  elif 'GNU AFFERO GENERAL PUBLIC LICENSE' in text:spdx='AGPL-3.0'
  elif 'Permission is hereby granted, free of charge' in text:spdx='MIT'
 return key,{'status':'READ','repo':repo,'revision':sha,'path':d['path'],'url':f"https://github.com/{repo}/blob/{sha}/{d['path']}", 'license_spdx':spdx, 'api_license_spdx':(d.get('license') or {}).get('spdx_id'), 'observed_utc':now,'http_status':200,'sha256':hashlib.sha256(content).hexdigest(),'artifact':str(artifact.relative_to(ROOT)), 'excerpt':text[:500]}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
 for key,value in executor.map(collect,sorted(targets)):existing[key]=value
output.write_text(json.dumps(existing,ensure_ascii=False,indent=2))
print(json.dumps({'revisions':len(targets),'read':sum(existing[r+'@'+s]['status']=='READ' for r,s in targets),'unresolved':[key for key,v in existing.items() if v['status']!='READ']},ensure_ascii=False))
