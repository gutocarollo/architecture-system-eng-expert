"""Prepare the authorized Jira Story with its exact ADF and catalog audit."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def inline(text):
    nodes = []
    for part in re.split(r"(\*\*[^*]+\*\*|https?://[^\s]+)", text):
        if not part:
            continue
        node = {"type": "text", "text": part}
        if part.startswith("**") and part.endswith("**"):
            node["text"] = part[2:-2]
            node["marks"] = [{"type": "strong"}]
        elif part.startswith(("http://", "https://")):
            address = part.rstrip(".,;")
            node["text"] = address
            node["marks"] = [{"type": "link", "attrs": {"href": address}}]
            nodes.append(node)
            if address != part:
                nodes.append({"type": "text", "text": part[len(address):]})
            continue
        nodes.append(node)
    return nodes


def paragraph(text):
    return {"type": "paragraph", "content": inline(text)}


def document(markdown):
    nodes = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip():
            continue
        heading = re.match(r"^(#{1,6}) (.*)$", line)
        if heading:
            nodes.append({"type": "heading", "attrs": {"level": len(heading[1])}, "content": inline(heading[2])})
            continue
        item = re.match(r"^(?:(\d+)\. |(-) )(.*)$", line)
        if item:
            kind = "orderedList" if item[1] else "bulletList"
            entries = [{"type": "listItem", "content": [paragraph(item[3])]}]
            while index < len(lines):
                next_item = re.match(r"^(?:(\d+)\. |(-) )(.*)$", lines[index])
                if not next_item or bool(next_item[1]) != bool(item[1]):
                    break
                entries.append({"type": "listItem", "content": [paragraph(next_item[3])]})
                index += 1
            node = {"type": kind, "content": entries}
            if kind == "orderedList":
                node["attrs"] = {"order": int(item[1])}
            nodes.append(node)
            continue
        parts = [line]
        while index < len(lines) and lines[index].strip():
            if re.match(r"^(#{1,6} |\d+\. |- )", lines[index]):
                break
            parts.append(lines[index])
            index += 1
        nodes.append(paragraph(" ".join(parts)))
    return {"type": "doc", "version": 1, "content": nodes}


def write_json(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


markdown = (ROOT / "story.md").read_text()
adf = document(markdown)
decision = json.loads((ROOT / "catalog-decision.json").read_text())
fields = decision["fields_example"]
fields["summary"] = markdown.splitlines()[0][2:]
fields["customfield_10054"] = adf
fields["reporter"] = {"accountId": "712020:88717512-e2a9-4849-a824-305d06874f48"}
fields["priority"] = {"id": "3"}
fields.pop("customfield_10521")
audit = decision["audit"]
audit["proposal_sha256"] = hashlib.sha256(json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
audit["proposal_prepared_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
fields["customfield_10521"] = {
    "type": "doc", "version": 1, "content": [
        paragraph("O catálogo permanece blocked porque o repositório material e o objeto do curso não foram resolvidos. Os campos de negócio e de página ficam vazios por não se aplicarem à alteração."),
        {"type": "codeBlock", "content": [{"type": "text", "text": "CATALOG_AUDIT_JSON=" + json.dumps(audit, ensure_ascii=False, separators=(",", ":"))}]},
    ],
}
request = {
    "cloudId": "941be6d6-e8c6-481a-9346-6c425e72d22f",
    "projectKey": "FBI", "issueTypeName": "Story",
    "summary": fields["summary"], "contentFormat": "adf", "responseContentFormat": "adf",
    "additional_fields": {key: value for key, value in fields.items() if key not in {"project", "issuetype", "summary"}},
}
write_json("story.adf.json", adf)
write_json("jira-create-request.json", request)
write_json("jira-create-preview.json", {"tool_name": "createJiraIssue", "tool_input": request})
write_json("jira-expected-fields.json", fields)
write_json("catalog-audit-final.json", audit)
print(json.dumps({"summary": fields["summary"], "adf_blocks": len(adf["content"]), "markdown_bytes": len(markdown.encode()), "proposal_sha256": audit["proposal_sha256"]}, ensure_ascii=False))
