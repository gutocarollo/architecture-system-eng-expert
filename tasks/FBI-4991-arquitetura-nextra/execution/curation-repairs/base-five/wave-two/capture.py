import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
CAPTURE_DIR = ROOT / 'raw'
CAPTURE_DIR.mkdir(exist_ok=True)

def capture(item):
    url = item['raw_url']
    record = dict(item)
    record['observed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'FBI-4991-primary-source-curation'}), timeout=35) as response:
            data = response.read()
            record['http_status'] = response.status
        filename = hashlib.sha256(url.encode()).hexdigest() + '.txt'
        target = CAPTURE_DIR / filename
        target.write_bytes(data)
        record['sha256'] = hashlib.sha256(data).hexdigest()
        record['artifact'] = str(target.relative_to(pathlib.Path.cwd()))
        record['line_count'] = len(data.splitlines())
    except urllib.error.HTTPError as error:
        record['http_status'] = error.code
        record['error'] = str(error)
    except Exception as error:
        record['error'] = str(error)
    return record

if __name__ == '__main__':
    items = json.loads((ROOT / 'capture-requests.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(capture, items))
    (ROOT / 'captures.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    for item in records:
        print(item['repo'],item['path'],item.get('http_status'),item.get('line_count'),item.get('error',''))
