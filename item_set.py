from analyze import BuildAnalyzer
from data import champion_keys
import json
import os
import zipfile
from pathlib import Path


def rounded(num):
    if num < 1.1:
        return 1
    elif num < 2:
        return 2
    else:
        return int(num)


class ItemSetBuilder:

    __analyzer = None

    def __init__(self, analyzer):
        if type(analyzer) is BuildAnalyzer:
            self.__analyzer = analyzer
        else:
            raise Exception("Analyzer is not valid")

    def starting_items(self):
        items = []
        for item in self.__analyzer.starting_items:
            if item["percentage"] > 50:
                items.append({
                    "id": str(item["item_id"]),
                    "count": rounded(item["avg_count"])
                })
        return items

    def items(self, l):
        items = []
        for item in sorted(l,
                           key=lambda x: x["percentage"],
                           reverse=True):
                if item["percentage"] > 3:
                    items.append({
                        "id": str(item["item_id"]),
                        "count": rounded(item["avg_count"])
                    })
        return items

    def generate(self):
        d = {
            "title": "CB for {0} ({1} games)".format(
                self.__analyzer.championKey,
                self.__analyzer.gameCount),
            "type": "custom",
            "map": "SR",
            "mode": "CLASSIC",
            "blocks": [
                {
                    "type": "Starting items",
                    "items": self.starting_items()
                },
                {
                    "type": "Offensive items",
                    "items": self.items(self.__analyzer.offensive_items)
                },
                {
                    "type": "Defensive items",
                    "items": self.items(self.__analyzer.defensive_items)
                },
                {
                    "type": "Other items",
                    "items": self.items(self.__analyzer.other_items)
                },
                {
                    "type": "Consumables",
                    "items": self.items(self.__analyzer.consumables)
                }
            ]
        }
        return d


def create_directories():
    for key in champion_keys():
        path = Path.cwd().joinpath(Path("results/" + key + "/Recommended/"))
        if path.exists() is False:
            path.mkdir(parents=True)


def create_files():
    for key in champion_keys():
        path = Path.cwd().joinpath(
            Path("results/" + key + "/Recommended/" + key + ".json"))
        with path.open('w') as f:
            json.dump(
                ItemSetBuilder(BuildAnalyzer(key)).generate(),
                f,
                indent=2)


def create_zipfile():
    zf = zipfile.ZipFile('result.zip', mode='w', compression=zipfile.ZIP_LZMA)
    for key in champion_keys():
        fname = key + "/Recommended/" + key + ".json"
        j = json.dumps(
            ItemSetBuilder(BuildAnalyzer(key)).generate(),
            indent=2)
        zf.writestr(fname, j)
    zf.close()

if __name__ == "__main__":
    create_zipfile()
