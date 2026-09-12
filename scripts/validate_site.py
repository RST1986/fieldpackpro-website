#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [ROOT / "index.html", ROOT / "privacy.html", ROOT / "support.html"]
REQUIRED_FILES = [*HTML_FILES, ROOT / "Logo.svg", ROOT / "_headers"]
FORBIDDEN_TEXT = ("netlify.app", "http://")

class SiteParser(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.local_refs = []
        self.images_without_alt = []
        self.inline_handlers = []
        self.inline_scripts = 0
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "img" and not attrs.get("alt"):
            self.images_without_alt.append(attrs.get("src", "<missing-src>"))
        for key in attrs:
            if key.lower().startswith("on"):
                self.inline_handlers.append((tag, key))
        if tag == "script" and not attrs.get("src"):
            self.inline_scripts += 1
        for key in ("href", "src"):
            value = attrs.get(key)
            if not value or value.startswith(("#", "mailto:", "tel:", "data:")):
                continue
            parsed = urlparse(value)
            if parsed.scheme or parsed.netloc:
                continue
            self.local_refs.append(value.split("#", 1)[0].split("?", 1)[0])


def fail(message, errors):
    errors.append(message)


def main():
    errors = []
    for path in REQUIRED_FILES:
        if not path.exists():
            fail(f"missing required file: {path.relative_to(ROOT)}", errors)

    for path in HTML_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        for forbidden in FORBIDDEN_TEXT:
            if forbidden in lower:
                fail(f"{path.name}: forbidden reference {forbidden}", errors)
        parser = SiteParser(path)
        parser.feed(text)
        if parser.h1_count != 1:
            fail(f"{path.name}: expected exactly one h1, found {parser.h1_count}", errors)
        for src in parser.images_without_alt:
            fail(f"{path.name}: image missing alt text: {src}", errors)
        for tag, attr in parser.inline_handlers:
            fail(f"{path.name}: inline event handler forbidden: {tag}[{attr}]", errors)
        if parser.inline_scripts:
            fail(f"{path.name}: inline script blocks are forbidden", errors)
        for ref in parser.local_refs:
            target = (path.parent / ref).resolve()
            if ROOT not in target.parents and target != ROOT:
                fail(f"{path.name}: local reference escapes repository: {ref}", errors)
            elif not target.exists():
                fail(f"{path.name}: broken local reference: {ref}", errors)

    headers = (ROOT / "_headers").read_text(encoding="utf-8") if (ROOT / "_headers").exists() else ""
    required_headers = (
        "Content-Security-Policy:", "Strict-Transport-Security:",
        "Referrer-Policy:", "X-Content-Type-Options: nosniff",
        "X-Frame-Options: DENY", "Permissions-Policy:"
    )
    for header in required_headers:
        if header not in headers:
            fail(f"_headers: missing security control: {header}", errors)
    if "script-src 'self'" not in headers:
        fail("_headers: CSP must keep scripts self-only", errors)
    if "unsafe-inline" in re.sub(r"style-src[^;]+;", "", headers):
        fail("_headers: unsafe-inline must not be allowed for scripts", errors)

    if errors:
        print("FIELD_PACK_SITE_GATE=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("FIELD_PACK_SITE_GATE=PASS")
    print("NETLIFY_REFERENCES=0")
    print("STATIC_SECURITY_HEADERS=PASS")
    print("HTML_CONTRACTS=PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
