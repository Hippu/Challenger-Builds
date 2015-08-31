from datetime import datetime
from analyze import BuildAnalyzer
from item_set import ItemSetBuilder
import zipfile
from data import champion_keys, update_database
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "days",
    help="The amount of days of games to analyze for the item sets",
    type=int
)
args = parser.parse_args()

with open('templates/index.html', 'r') as f:
    template = f.read()


def create_index(path):
    index = template.format(
        timestamp=datetime.utcnow(),
        filename="item_set.zip")
    with open(path, mode='w') as f:
        f.write(index)


def create_zipfile(path):
    zf = zipfile.ZipFile(
        path, mode='w', compression=zipfile.ZIP_LZMA)
    for key in champion_keys():
        fname = key + "/Recommended/" + key + ".json"
        j = json.dumps(
            ItemSetBuilder(BuildAnalyzer(key)).generate(),
            indent=2)
        zf.writestr(fname, j)
    zf.close()

if __name__ == "__main__":
    update_database(days=args.days)
    path = 'target/'
    create_index(path + 'index.html')
    create_zipfile(path + 'item_set.zip')
