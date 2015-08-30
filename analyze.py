import riot_api
from data import (
    engine, Champion, BoughtItems, Session, is_final_item,
    get_item_set, ItemTags)
from sqlalchemy.sql import select, func


def count_champions_in_match_set(matches):
    result = {}
    for match in matches:
        champions = []
        if "participants" in match:
            for participant in match["participants"]:
                champions.append(participant["championId"])
            for champion in champions:
                if champion in result:
                    result[champion] += 1
                else:
                    result.update({champion: 1})
    champions = riot_api.get_champions()["data"]
    pretty_result = []
    for key, value in result.items():
        pretty_result.append((champions[str(key)]["key"], value))
    pretty_result.sort(key=lambda x: x[1], reverse=True)
    return pretty_result


def get_matches_without_timelines(matches):
    matches_without = 0
    for match in matches:
        if "timeline" not in match:
            matches_without += 1

    return matches_without


class BuildAnalyzer:
    championKey = None
    gameCount = None

    def __init__(self, championKey=None):
        self.championKey = championKey
        if self.championKey is None:
            raise Exception("Champion key can't be None")
        self.gameCount = self.game_count()
        self.__cache = {}

    def game_count(self):
        s = Session()
        gameCount = s.query(Champion).filter(
            Champion.champion_key == self.championKey).count()
        return gameCount

    @property
    def starting_items(self):
        if "starting_items" in self.__cache:
            return self.__cache["starting_items"]

        s = select([
            Champion.champion_key,
            BoughtItems.item_id,
            func.count(BoughtItems.item_id)]).\
            distinct(BoughtItems.item_id).\
            group_by(BoughtItems.item_id).\
            order_by(func.count(BoughtItems.item_id)).\
            select_from(
                Champion.__table__.join(
                    BoughtItems,
                    onclause=Champion.match_id == BoughtItems.match_id)).\
            where(Champion.champion_key == self.championKey).\
            where(Champion.participant_id == BoughtItems.participant_id).\
            where(BoughtItems.timestamp < 110 * 1000)

        with engine.connect() as conn:
            items = []
            result = conn.execute(s)
            for row in result:
                items.append({
                    "item_id": row[1],
                    "avg_count": row[2] / self.gameCount,
                    "percentage": row[2] / self.gameCount * 100
                })
            # Put results to cache
            self.__cache.update({"starting_items": items})
            return items

    @property
    def items(self):
        if "items" in self.__cache:
            return self.__cache["items"]

        s = select([
            Champion.champion_key,
            BoughtItems.item_id,
            func.count(BoughtItems.item_id)]).\
            distinct(BoughtItems.item_id).\
            group_by(BoughtItems.item_id).\
            order_by(func.count(BoughtItems.item_id)).\
            select_from(
                Champion.__table__.join(
                    BoughtItems,
                    onclause=Champion.match_id == BoughtItems.match_id)).\
            where(Champion.champion_key == self.championKey).\
            where(Champion.participant_id == BoughtItems.participant_id).\
            where(BoughtItems.timestamp > 110 * 1000)

        with engine.connect() as conn:
            items = []
            result = conn.execute(s)
            for row in result:
                if is_final_item(row[1]):
                    items.append({
                        "item_id": row[1],
                        "avg_count": row[2] / self.gameCount,
                        "percentage": row[2] / self.gameCount * 100
                    })
            # Put results to cache
            self.__cache.update({"items": items})
            return items

    @property
    def offensive_items(self):
        if "offensive_items" in self.__cache:
            return self.__cache["offensive_items"]

        off = [x for x in self.items if x["item_id"]
               in get_item_set(ItemTags.offensive)]

        self.__cache.update({"offensive_items": off})
        return off

    @property
    def defensive_items(self):
        if "defensive_items" in self.__cache:
            return self.__cache["defensive_items"]

        items = [x for x in self.items if x["item_id"]
                 in get_item_set(ItemTags.defensive)]

        self.__cache.update({"defensive_items": items})
        return items

    @property
    def other_items(self):
        if "other" in self.__cache:
            return self.__cache["other"]

        other = [item for item in self.items if item not in
                 (self.offensive_items
                  + self.defensive_items
                  + self.consumables)]

        self.__cache.update({"other": other})
        return other

    @property
    def consumables(self):
        if "consumables" in self.__cache:
            return self.__cache["consumables"]

        consumables = [x for x in self.items if x["item_id"]
                       in get_item_set(ItemTags.consumable)]

        self.__cache.update({"consumables": consumables})

        return consumables


if __name__ == '__main__':
    b = BuildAnalyzer("Azir")
    # print(b.starting_items)
    # print(b.offensive_items)
    print(b.other_items)
