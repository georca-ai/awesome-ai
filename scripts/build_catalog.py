#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"{path.name}: {error}") from error


def index(items, kind):
    indexed = {}
    for item in items:
        key = item["id"]
        if not ID.fullmatch(key):
            raise ValueError(f"Invalid {kind} ID: {key}")
        if key in indexed:
            raise ValueError(f"Duplicate {kind} ID: {key}")
        indexed[key] = item
    return indexed


def check_copy(copy, expected, label):
    missing = expected - copy.keys()
    extra = copy.keys() - expected
    if missing or extra:
        raise ValueError(f"{label}: missing {sorted(missing)}, unknown {sorted(extra)}")
    for key, value in copy.items():
        if not isinstance(value, str) or not value.strip() or len(value.splitlines()) != 1:
            raise ValueError(f"{label}: expected one line of text for {key}")


def page_path(locale):
    return Path("README.md") if locale == "en" else Path("docs", locale, "README.md")


def relative_link(source, target):
    return Path(os.path.relpath(target, source.parent)).as_posix()


def render(locale, locales, categories, tools, copy):
    page = page_path(locale)
    language_links = [
        f"**{item['name']}**" if key == locale
        else f"[{item['name']}]({relative_link(page, page_path(key))})"
        for key, item in locales.items()
    ]
    labels = copy["page"]
    lines = [f"# {labels['title']}", "", " · ".join(language_links), ""]
    if locales[locale].get("rtl"):
        lines.extend([f'<div dir="rtl" lang="{locale}">', ""])
    lines.extend([labels["intro"], "", f"## {labels['contents']}", ""])
    for key in categories:
        lines.append(f"- [{copy['categories'][key]}](#category-{key})")
    for key in categories:
        lines.extend(["", f'<a name="category-{key}"></a>', "",
                      f"## {copy['categories'][key]}", ""])
        for tool_id, tool in tools.items():
            if tool["category"] == key:
                lines.append(f"- [{tool['name']}]({tool['url']}) — {copy['tools'][tool_id]}")
    contributing = relative_link(page, Path("CONTRIBUTING.md"))
    lines.extend(["", f"[{labels['contribute']}]({contributing})"])
    if locales[locale].get("rtl"):
        lines.extend(["", "</div>"])
    return "\n".join(lines) + "\n"


def build_pages(root):
    data = root / "data"
    catalog = read_json(data / "catalog.json")
    locales = index(catalog["locales"], "locale")
    categories = index(catalog["categories"], "category")
    tools = index(catalog["tools"], "tool")
    if "en" not in locales:
        raise ValueError("The English locale is required for the root README")
    for key, tool in tools.items():
        category = tool["category"]
        if category not in categories:
            raise ValueError(f"Unknown category for {key}: {category}")
        url = urlsplit(tool["url"])
        if url.scheme != "https" or not url.hostname or re.search(r"[\s()<>]", tool["url"]):
            raise ValueError(f"{key}: expected a Markdown-safe HTTPS URL")

    pages = {}
    for locale in locales:
        copy = read_json(data / "locales" / f"{locale}.json")
        check_copy(copy["page"], {"title", "intro", "contents", "contribute"}, f"{locale} page")
        check_copy(copy["categories"], categories.keys(), f"{locale} categories")
        check_copy(copy["tools"], tools.keys(), f"{locale} tools")
        pages[page_path(locale)] = render(locale, locales, categories, tools, copy)
    return pages


def main():
    parser = argparse.ArgumentParser(description="Build localized catalog pages.")
    parser.add_argument("--check", action="store_true", help="Check without writing files.")
    args = parser.parse_args()
    try:
        pages = build_pages(ROOT)
        stale = []
        for path, content in pages.items():
            destination = ROOT / path
            if args.check:
                if not destination.is_file() or destination.read_bytes() != content.encode("utf-8"):
                    stale.append(path.as_posix())
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8", newline="\n")
        if stale:
            print("Run python3 scripts/build_catalog.py to refresh: " + ", ".join(stale),
                  file=sys.stderr)
            return 1
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
