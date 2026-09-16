from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def parse_markdown(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            body = text[end + 5 :].lstrip("\n")
            for line in text[4:end].splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] == '"':
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass
                meta[key.strip()] = value
    return meta, body


def plain_text(markdown: str) -> str:
    text = re.sub(r"```[^\n]*\n(.*?)```", r"\1", markdown, flags=re.S)
    text = re.sub(r"!\[([^]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"^[>#*+\-\d.()\s]+", "", text, flags=re.M)
    return re.sub(r"\s+", " ", text).strip()


def main(package: Path) -> int:
    references = package / "harmonyos" / "references"
    if not references.is_dir():
        print(f"references directory not found: {references}", file=sys.stderr)
        return 2

    indexed_paths: set[Path] = set()
    for category_dir in sorted(path for path in references.iterdir() if path.is_dir()):
        index_path = category_dir / "INDEX.md"
        if not index_path.is_file():
            continue
        for target in re.findall(r"\]\(([^)#?]+\.md)(?:#[^)]*)?\)", index_path.read_text(encoding="utf-8")):
            candidate = (category_dir / target).resolve()
            if candidate.is_file() and references.resolve() in candidate.parents:
                indexed_paths.add(candidate)

    source_paths = sorted(indexed_paths) if indexed_paths else sorted(references.glob("*/*.md"))
    records: list[dict[str, object]] = []
    category_counts: Counter[str] = Counter()
    category_bytes: Counter[str] = Counter()
    missing: list[str] = []

    for path in source_paths:
        if path.name.casefold() == "index.md":
            continue
        meta, body = parse_markdown(path)
        category = meta.get("category") or path.parent.name
        relative = path.relative_to(package).as_posix()
        record: dict[str, object] = {
            "id": path.stem,
            "title": meta.get("title", path.stem),
            "breadcrumb": meta.get("breadcrumb", ""),
            "category": category,
            "url": meta.get("url", ""),
            "doc_updated_at": meta.get("doc_updated_at") or None,
            "scraped_at": meta.get("scraped_at") or None,
            "content_hash": meta.get("content_hash") or None,
            "path": relative,
            "chars": len(body),
            "text": plain_text(body),
        }
        if category == "harmonyos-faqs":
            record["markdown"] = body
        records.append(record)
        category_counts[category] += 1
        category_bytes[category] += path.stat().st_size
        if not record["url"] or not record["title"]:
            missing.append(relative)

    faq_records = [record for record in records if record["category"] == "harmonyos-faqs"]
    with (package / "faq-corpus.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in faq_records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    with (package / "catalog.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            metadata = {key: value for key, value in record.items() if key not in {"text", "markdown"}}
            handle.write(json.dumps(metadata, ensure_ascii=False, separators=(",", ":")) + "\n")

    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    rebuilt_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    target = next((record for record in faq_records if record["id"] == "faqs-arkui-500"), None)
    manifest.update(
        {
            "last_local_index_rebuild_at": rebuilt_at,
            "document_count": len(records),
            "faq_count": len(faq_records),
            "categories": dict(sorted(category_counts.items())),
            "category_source_bytes": dict(sorted(category_bytes.items())),
            "requested_document_present": target is not None,
            "requested_document": target,
            "missing_required_metadata_count": len(missing),
            "missing_required_metadata_paths": missing[:100],
        }
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    digest = hashlib.sha256()
    for path in sorted(package.rglob("*")):
        if not path.is_file() or path.name in {"CONTENT_SHA256.txt", "SHA256SUMS.txt"}:
            continue
        relative = path.relative_to(package)
        if any(part in {".venv", "__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        if len(relative.parts) >= 2 and relative.parts[:2] == ("scraper", "data"):
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    (package / "CONTENT_SHA256.txt").write_text(
        f"{digest.hexdigest()}  HarmonyOS-Docs-AI directory-content\n", encoding="ascii"
    )
    print(
        json.dumps(
            {
                "ok": not missing,
                "rebuilt_at": rebuilt_at,
                "document_count": len(records),
                "faq_count": len(faq_records),
                "missing_required_metadata_count": len(missing),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not missing else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: rebuild_indexes.py <package-root>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
