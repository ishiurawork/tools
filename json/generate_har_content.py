#!/usr/bin/env python3
import json, sys, argparse, jmespath
from pathlib import Path

def nest(keys: list[str], value) -> dict:
    """['a','b','c'], v  → {'a':{'b':{'c': v}}}"""
    d = value
    for k in reversed(keys):
        d = {k: d}
    return d

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("har", type=Path, help="HAR file")
    ap.add_argument("--expr", required=True,
                    help="JMESPath expression after log.entries[] (e.g. request.url)")
    ap.add_argument("--filter", default='/(click|imp)',
                    help="grep -E 相当のフィルタ正規表現")
    args = ap.parse_args()

    har = json.loads(args.har.read_text())

    # 1️⃣ JMESPath で全エントリを取得
    entries = jmespath.search("log.entries", har) or []

    import re
    pat = re.compile(args.filter)

    values = []
    for e in entries:
        v = jmespath.search(args.expr, e)
        if v is not None:
            v_str = str(v)
            if pat.search(v_str):
                values.append(v)

    # 2️⃣ ネストを復元
    key_chain = args.expr.split(".")
    snippet = {
        "log": {
            "entries": [nest(key_chain, v) for v in values]
        }
    }
    print(json.dumps(snippet, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
