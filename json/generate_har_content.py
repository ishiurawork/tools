#!/usr/bin/env python3
# generate_har_content.py
import argparse, json, re, sys
from pathlib import Path
import jmespath

def nest(keys: list[str], value):
    """['a','b','c'], v → {'a':{'b':{'c': v}}}"""
    d = value
    for k in reversed(keys):
        d = {k: d}
    return d

def deep_merge(dst: dict, src: dict) -> dict:
    """src を dst に再帰マージして返す"""
    for k, v in src.items():
        if k in dst and isinstance(dst[k], dict) and isinstance(v, dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("har", type=Path, help="HAR file")
    ap.add_argument("--expr1", required=True,
                    help="JMESPath expr after log.entries[]  (例: response.status)")
    ap.add_argument("--expr2", required=True,
                    help="JMESPath expr after log.entries[]  (例: request.url)")
    ap.add_argument("--expr3", required=True,
                    help="JMESPath expr after log.entries[]  (例: request.method)")
    ap.add_argument("--filter", default='/(click|imp)',
                    help="expr2 に対して適用する grep -E 相当の正規表現")
    args = ap.parse_args()

    har = json.loads(args.har.read_text())
    entries = jmespath.search("log.entries", har) or []

    pat = re.compile(args.filter)
    key1, key2, key3 = args.expr1.split("."), args.expr2.split("."), args.expr3.split(".")

    snippets = []
    for e in entries:
        v1 = jmespath.search(args.expr1, e)
        v2 = jmespath.search(args.expr2, e)
        v3 = jmespath.search(args.expr3, e)
        # expr2 の値が str でフィルタに合致するものだけ採用
        if isinstance(v2, str) and pat.search(v2):
            d = deep_merge(nest(key1, v1), nest(key2, v2))
            d = deep_merge(d, nest(key3, v3))
            snippets.append(d)

    print(json.dumps({"log": {"entries": snippets}},
                     ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
