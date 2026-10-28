from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
import datetime
import hashlib
import json
import sys


ROOT = Path("tasks/FBI-4991-arquitetura-nextra/execution")
OUTPUT = ROOT / "curation-repairs/rare-security"
cache = []
for path in [ROOT / "curation/sources.json", ROOT / "curation-repairs/sources.json"]:
    data = json.loads(path.read_text())
    cache.extend(data.values() if isinstance(data, dict) else data)


def capture(item):
    repo, revision, path = item
    destination = OUTPUT / (repo.replace("/", "--") + "--" + revision[:8] + "--" + path.replace("/", "--"))
    receipt_path = destination.with_name(destination.name + ".receipt.json")
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        assert hashlib.sha256(destination.read_bytes()).hexdigest() == receipt["sha256"]
        return {"repo": repo, "path": path, "source": "owned_cache", "line_count": receipt["line_count"]}
    cached = next((source for source in cache if source.get("repo") == repo and source.get("revision") == revision and source.get("path") == path and source.get("http_status") == 200 and Path(source.get("artifact", "")).is_file()), None)
    try:
        if cached:
            data = Path(cached["artifact"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == cached["sha256"]
        else:
            with urlopen(Request(f"https://raw.githubusercontent.com/{repo}/{revision}/{path}", headers={"User-Agent": "architecture-source-curation"}), timeout=40) as response:
                data = response.read()
        destination.write_bytes(data)
        receipt = {"repo": repo, "revision": revision, "path": path, "url": f"https://github.com/{repo}/blob/{revision}/{path}", "raw_url": f"https://raw.githubusercontent.com/{repo}/{revision}/{path}", "artifact": str(destination), "http_status": 200, "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "sha256": hashlib.sha256(data).hexdigest(), "line_count": len(data.splitlines()), "source": "reused_cache" if cached else "raw_primary"}
        if cached:
            receipt["cache_artifact"] = cached["artifact"]
            receipt["upstream_observed_utc"] = cached.get("observed_utc")
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        return {key: receipt[key] for key in ["repo", "path", "source", "line_count"]}
    except Exception as error:
        return {"repo": repo, "revision": revision, "path": path, "error": str(error)}


if __name__ == "__main__":
    requests = json.loads(sys.stdin.read())
    with ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(capture, requests):
            print(json.dumps(result))
