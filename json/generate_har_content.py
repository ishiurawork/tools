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

def merge_partial_json(files: list[Path]) -> dict:
    """複数の {"log":{"entries":[...]}} を entries のインデックスでマージ"""
    parts = [json.loads(p.read_text()) for p in files]
    # entries 配列の長さが異なる場合は最小に合わせる
    lengths = [len(p["log"]["entries"]) for p in parts]
    min_len = min(lengths)

    merged_entries = []
    for i in range(min_len):
        m = {}
        for p in parts:
            deep_merge(m, p["log"]["entries"][i])
        merged_entries.append(m)

    return {"log": {"entries": merged_entries}}

def extract_from_har(args) -> dict:
    """HAR から expr1〜expr3 を抜き取って JSON 生成"""
    har = json.loads(args.extract_har.read_text())
    entries = jmespath.search("log.entries", har) or []

    pat = re.compile(args.filter)
    key1, key2, key3 = args.expr1.split("."), args.expr2.split("."), args.expr3.split(".")

    snippets = []
    for e in entries:
        v1 = jmespath.search(args.expr1, e)
        v2 = jmespath.search(args.expr2, e)
        v3 = jmespath.search(args.expr3, e)

        target_value = [v1, v2, v3][args.filter_apply_no - 1]
        if isinstance(target_value, str) and pat.search(target_value):
            d = deep_merge(nest(key1, v1), nest(key2, v2))
            d = deep_merge(d, nest(key3, v3))
            snippets.append(d)

    return {"log": {"entries": snippets}}

def main() -> None:
    ap = argparse.ArgumentParser()
    mx = ap.add_mutually_exclusive_group(required=True)
    mx.add_argument("--extract-har", type=Path,
                    help="入力 HAR ファイル。expr1〜3 と併用")
    mx.add_argument("--partial-json-files", nargs="+", type=Path,
                    metavar="JSON", help="部分 JSON ファイルをマージ")

    # extract-har 用オプション
    ap.add_argument("--expr1", help="JMESPath after log.entries[] 例: response.status")
    ap.add_argument("--expr2", help="同上 例: request.url")
    ap.add_argument("--expr3", help="同上 例: request.method")
    ap.add_argument("--filter", default='/(click|imp)',
                    help="正規表現フィルタ (default: '/(click|imp)')")
    ap.add_argument("--filter-apply-no", choices=[1, 2, 3], type=int, default=2,
                    help="フィルタを適用する expr の番号 (1/2/3)")

    args = ap.parse_args()

    if args.partial_json_files:
        result = merge_partial_json(args.partial_json_files)
    else:
        # expr1〜3 必須チェック
        for name in ("expr1", "expr2", "expr3"):
            if getattr(args, name) is None:
                sys.exit(f"--extract-har を使う場合 {name} が必須です")
        result = extract_from_har(args)

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
