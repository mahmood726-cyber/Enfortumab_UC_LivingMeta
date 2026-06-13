# sentinel:skip-file -- this test intentionally contains the placeholder
# tokens ({{...}}, REPLACE_ME, __PLACEHOLDER__) it scans the dashboard for.
"""Minimal structural smoke test for the Enfortumab UC LivingMeta dashboard.

The repo ships a single-file HTML living meta-analysis app (no build step, no
JS test runner). This test guards the structural invariants that, if broken,
silently corrupt the rendered dashboard:

  * no UTF-8 BOM (breaks `<!doctype>` sniffing / strict parsers)
  * <script> / </script> tags balance (a stray literal </script> inside a
    template literal truncates the script block)
  * no unfilled build placeholders ({{...}} build tokens, REPLACE_ME, __PLACEHOLDER__)
  * the redirect stub (index.html) points at the dashboard file

Run:  python -m pytest -q   (or)  python test_smoke.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(HERE, "ENFORTUMAB_UC_REVIEW.html")
INDEX = os.path.join(HERE, "index.html")


def _read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def test_dashboard_exists():
    assert os.path.exists(DASH), "dashboard HTML missing"
    assert os.path.getsize(DASH) > 100_000, "dashboard unexpectedly small"


def test_no_bom():
    assert _read_bytes(DASH)[:3] != b"\xef\xbb\xbf", "dashboard has a UTF-8 BOM"
    assert _read_bytes(INDEX)[:3] != b"\xef\xbb\xbf", "index.html has a UTF-8 BOM"


def test_script_tags_balanced():
    s = _read_bytes(DASH).decode("utf-8", errors="replace")
    opens = len(re.findall(r"<script[\s>]", s))
    closes = s.count("</script>")
    assert opens == closes, f"<script> ({opens}) != </script> ({closes})"


def test_no_unfilled_placeholders():
    s = _read_bytes(DASH).decode("utf-8", errors="replace")
    # `${{...}}` is a legitimate JS object-literal inside a template literal;
    # an unfilled build token is a bare `{{name}}` not preceded by `$`.
    bare_braces = re.findall(r"(?<!\$)\{\{[a-zA-Z_][\w.\- ]*\}\}", s)
    assert not bare_braces, f"unfilled build placeholders: {bare_braces[:5]}"
    for token in ("REPLACE_ME", "__PLACEHOLDER__"):
        assert token not in s, f"placeholder token {token!r} present"


def test_index_redirects_to_dashboard():
    s = _read_bytes(INDEX).decode("utf-8", errors="replace")
    assert "ENFORTUMAB_UC_REVIEW.html" in s, "index stub does not reference dashboard"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all smoke tests passed")
