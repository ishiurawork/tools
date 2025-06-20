# Content


## json
例：.log.entries[].response.status を集めたい場合
python generate_har_content.py test_case1.har \
       --expr response.status \
       --filter '2..' > tmp_har.json

cat tmp_har.json
