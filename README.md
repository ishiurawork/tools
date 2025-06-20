# Content


## json
例：.log.entries[].response.status を集めたい場合
python generate_har_content.py --extract-har test_case1.har \
       --expr response.status \
       --filter '2..' > tmp_har.json

cat tmp_har.json

例：マージ（--partial-json-filesを使用）
python generate_har_content.py --extract-har test_case1.har ... > part1.json
python generate_har_content.py --extract-har test_case1.har ... > part2.json
python generate_har_content.py --partial-json-files part1.json part2.json > merged.json
