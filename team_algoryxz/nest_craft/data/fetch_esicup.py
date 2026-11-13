import urllib.request
import json
import os

url = 'https://api.github.com/repos/ESICUP/datasets/contents/2d_irregular'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    items = json.loads(resp.read().decode('utf-8'))
    print(f"Total items in ESICUP 2d_irregular: {len(items)}")
    for item in items:
        print(f"Name: {item['name']}, Type: {item['type']}, URL: {item.get('download_url')}")
