import urllib.request
import json
import os

for benchmark in ['shapes', 'dagli', 'fu', 'swim']:
    url = f'https://api.github.com/repos/ESICUP/datasets/contents/2d_irregular/{benchmark}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            files = json.loads(resp.read().decode('utf-8'))
            print(f"\n--- Benchmark: {benchmark} ({len(files)} files) ---")
            for f in files:
                print(f"  {f['name']} ({f['size']} bytes) -> {f['download_url']}")
    except Exception as e:
        print(f"Error fetching {benchmark}: {e}")
