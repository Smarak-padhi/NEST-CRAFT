import urllib.request
import os

os.makedirs('team_algoryxz/nest_craft/data/esicup', exist_ok=True)

files_to_download = {
    'shapes.txt': 'https://raw.githubusercontent.com/ESICUP/datasets/main/2d_irregular/shapes/shapes.txt',
    'shapes0.xml': 'https://raw.githubusercontent.com/ESICUP/datasets/main/2d_irregular/shapes/shapes0.xml',
    'readme_shapes.txt': 'https://raw.githubusercontent.com/ESICUP/datasets/main/2d_irregular/shapes/readme.txt',
    'swim.txt': 'https://raw.githubusercontent.com/ESICUP/datasets/main/2d_irregular/swim/swim.txt',
    'readme_dagli.txt': 'https://raw.githubusercontent.com/ESICUP/datasets/main/2d_irregular/dagli/readme.txt'
}

for name, url in files_to_download.items():
    dest = os.path.join('team_algoryxz/nest_craft/data/esicup', name)
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"Downloaded {name} ({os.path.getsize(dest)} bytes)")
    except Exception as e:
        print(f"Failed {name}: {e}")
