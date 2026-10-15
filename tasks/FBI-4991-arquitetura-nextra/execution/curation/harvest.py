#!/usr/bin/env python3
"""Collect dated primary repository, revision, license, and source receipts."""
import concurrent.futures
import datetime
import hashlib
import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).resolve().parent
RAW = OUTPUT / "raw"
RAW.mkdir(exist_ok=True)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def api(endpoint):
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
    if result.returncode:
        return {"error": result.stderr[:400], "observed_utc": now()}
    return json.loads(result.stdout)


def read_json(name, default):
    path = OUTPUT / name
    return json.loads(path.read_text()) if path.exists() else default


def download(url):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "FBI-4991-primary-curation"})
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, b""
    except Exception as error:
        return str(error), b""


sections = read_json("existing-sections.json", [])
urls = {url for section in sections for url in section["github_urls"]}
selections = read_json("source-selections.json", {})
for value in selections.values():
    for key in ("base_urls", "application_urls", "extra_urls", "skill_urls"):
        urls.update(value.get(key, []))
urls.update(read_json("additional-urls.json", []))
repos = sorted({"/".join(url.split("/")[3:5]) for url in urls if url.startswith("https://github.com/")})
metadata = read_json("github-metadata.json", {})


def collect_metadata(repo):
    data = api(f"repos/{repo}")
    if "error" in data:
        return repo, data
    return repo, {
        "repository": data["full_name"], "url": data["html_url"],
        "stars": data["stargazers_count"], "license_spdx": (data.get("license") or {}).get("spdx_id"),
        "license_name": (data.get("license") or {}).get("name"), "archived": data["archived"],
        "default_branch": data["default_branch"], "pushed_at": data["pushed_at"],
        "observed_utc": now(), "api_url": f"https://api.github.com/repos/{repo}", "http_status": 200,
    }


missing = [repo for repo in repos if repo not in metadata or "error" in metadata[repo]]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    for repo, item in executor.map(collect_metadata, missing):
        metadata[repo] = item
(OUTPUT / "github-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
print(f"Metadata: {len(metadata)} repositories; {sum('error' in x for x in metadata.values())} errors", flush=True)
revisions = read_json("revisions.json", {})
targets = set()
for url in urls:
    parts = url.split("/")
    repo = "/".join(parts[3:5])
    if len(parts) > 6 and parts[5] in ("blob", "tree"):
        ref = parts[6]
    else:
        ref = metadata.get(repo, {}).get("default_branch", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        targets.add((repo, ref))


def collect_revision(target):
    repo, ref = target
    data = api(f"repos/{repo}/commits/{urllib.parse.quote(ref, safe='')}")
    return f"{repo}@{ref}", {"sha": data.get("sha"), "observed_utc": now(), "error": data.get("error")}


missing = [target for target in targets if not revisions.get(f"{target[0]}@{target[1]}", {}).get("sha")]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    revisions.update(executor.map(collect_revision, missing))
(OUTPUT / "revisions.json").write_text(json.dumps(revisions, indent=2))
print(f"Revisions: {len(revisions)} resolved refs", flush=True)
licenses = read_json("licenses.json", {})


def collect_license(repo):
    ref = metadata.get(repo, {}).get("default_branch", "HEAD")
    sha = revisions.get(f"{repo}@{ref}", {}).get("sha") or ref
    data = api(f"repos/{repo}/license?ref={sha}")
    if "error" in data:
        return repo, {"status": "UNRESOLVED", "observed_utc": now(), "error": data["error"], "ref": sha}
    status, content = download(data["download_url"])
    path = RAW / (hashlib.sha256(data["download_url"].encode()).hexdigest() + ".txt")
    path.write_bytes(content)
    return repo, {"status": "READ" if status == 200 else "UNRESOLVED", "observed_utc": now(),
                  "license_spdx": (data.get("license") or {}).get("spdx_id"), "path": data["path"],
                  "url": f"https://github.com/{repo}/blob/{sha}/{data['path']}", "ref": sha,
                  "http_status": status, "sha256": hashlib.sha256(content).hexdigest(),
                  "artifact": str(path.relative_to(ROOT)), "excerpt": content.decode(errors="replace")[:800]}


missing = [repo for repo in repos if repo not in licenses]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    licenses.update(executor.map(collect_license, missing))
(OUTPUT / "licenses.json").write_text(json.dumps(licenses, ensure_ascii=False, indent=2))
print(f"Licenses: {sum(x['status']=='READ' for x in licenses.values())} read / {len(licenses)}", flush=True)
sources = read_json("sources.json", {})


def collect_source(url):
    parts = urllib.parse.urlsplit(url)
    tokens = parts.path.strip("/").split("/")
    if len(tokens) < 5 or tokens[2] != "blob":
        repo = "/".join(tokens[:2])
        ref = tokens[3] if len(tokens) > 3 and tokens[2] == "tree" else metadata.get(repo, {}).get("default_branch", "HEAD")
        sha = ref if re.fullmatch(r"[0-9a-f]{40}", ref) else revisions.get(f"{repo}@{ref}", {}).get("sha")
        source_path = "/".join(tokens[4:]) if len(tokens) > 4 and tokens[2] == "tree" else ""
        fixed = f"https://github.com/{repo}/tree/{sha}" + (f"/{source_path}" if source_path else "") if sha else url
        return url, {"kind": "REPOSITORY_OR_DIRECTORY", "repo": repo, "path": source_path,
                     "revision": sha, "url": fixed, "original_url": url, "observed_utc": now(),
                     "status": "REVISION_RESOLVED" if sha else "UNRESOLVED_REVISION"}
    repo = "/".join(tokens[:2])
    ref = tokens[3]
    sha = ref if re.fullmatch(r"[0-9a-f]{40}", ref) else revisions.get(f"{repo}@{ref}", {}).get("sha")
    if not sha:
        return url, {"kind": "UNRESOLVED_REVISION", "url": url, "repo": repo, "ref": ref}
    source_path = "/".join(tokens[4:])
    raw_url = f"https://raw.githubusercontent.com/{repo}/{sha}/{source_path}"
    status, content = download(raw_url)
    artifact = RAW / (hashlib.sha256(raw_url.encode()).hexdigest() + ".txt")
    if content:
        artifact.write_bytes(content)
    lines = content.decode(errors="replace").splitlines()
    anchor = re.fullmatch(r"L(\d+)(?:-L(\d+))?", parts.fragment)
    start = int(anchor.group(1)) if anchor else 1
    end = int(anchor.group(2) or start) if anchor else min(40, len(lines))
    excerpt = "\n".join(f"{number}: {lines[number-1]}" for number in range(start, min(end, len(lines))+1))
    return url, {"kind": "FILE", "repo": repo, "path": source_path, "revision": sha,
                 "original_url": url, "url": f"https://github.com/{repo}/blob/{sha}/{source_path}" + (f"#{parts.fragment}" if parts.fragment else ""),
                 "raw_url": raw_url, "http_status": status, "observed_utc": now(),
                 "sha256": hashlib.sha256(content).hexdigest(), "line_count": len(lines),
                 "artifact": str(artifact.relative_to(ROOT)), "excerpt_lines": [start, end], "excerpt": excerpt}


missing = [url for url in sorted(urls) if url not in sources or (sources[url].get("kind") == "REPOSITORY_OR_DIRECTORY" and not sources[url].get("revision"))]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
    for url, item in executor.map(collect_source, missing):
        sources[url] = item
(OUTPUT / "sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2))
files = [x for x in sources.values() if x["kind"] == "FILE"]
print(f"Sources: {len(files)} files; {sum(x['http_status']==200 for x in files)} HTTP 200; {len(sources)} total locators", flush=True)
