from datetime import datetime
from analyze import BuildAnalyzer
from item_set import ItemSetBuilder
import zipfile
from data import champion_keys, update_database, create_db_from_scratch
import json
import argparse
from shutil import copytree, rmtree
from os import mkdir
from os.path import isdir
from riot_api import get_config

parser = argparse.ArgumentParser()
parser.add_argument(
    "days",
    help="The amount of days of games to analyze for the item sets",
    type=int
)
parser.add_argument(
    "--no-download",
    help="Don't use the api and only use the games that already exists \
    in the database",
    action="store_true"
)
parser.add_argument(
    "--create-database",
    help="Creates a new database and deletes the current one if it exists",
    action="store_true"
)
parser.add_argument(
    "--production",
    help="Removes api throttling, only use if you have a production api key \
    otherwise you are going to hit rate limits",
    action="store_true"
)
args = parser.parse_args()

with open('templates/index.html', 'r') as f:
    template = f.read()


def copy_static(path):
    copytree("templates/static/", path + "static/")


def create_index(path):
    index = template.format(
        timestamp=datetime.utcnow(),
        filename="item_set.zip",
        days=args.days)
    with open(path, mode='w') as f:
        f.write(index)


def create_zipfile(path):
    zf = zipfile.ZipFile(
        path, mode='w', compression=zipfile.ZIP_LZMA)
    for key in champion_keys():
        print("Building items for " + key)
        fname = key + "/Recommended/" + key + ".json"
        j = json.dumps(
            ItemSetBuilder(BuildAnalyzer(key, args.days)).generate(),
            indent=2)
        zf.writestr(fname, j)
    zf.close()

if __name__ == "__main__":
    if args.production:
        get_config().wait_time = 0.025
    if args.create_database:
        create_db_from_scratch()
    if not args.no_download:
        update_database(days=args.days)
    path = 'target/'
    # Clear the target directory
    if isdir(path):
        rmtree(path)
    mkdir(path)
    copy_static(path)
    create_index(path + 'index.html')
    create_zipfile(path + 'item_set.zip')
