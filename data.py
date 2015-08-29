from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Interval, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func, select
from datetime import datetime, timedelta
import riot_api
import pickle

engine = create_engine('sqlite:///data.db', echo=True)
Base = declarative_base()
Session = sessionmaker()
Session.configure(bind=engine)


class Match(Base):
    __tablename__ = 'matches'

    match_id = Column(Integer, primary_key=True)
    region = Column(String)
    created_on = Column(DateTime)
    duration = Column(Interval)
    items_bought = relationship("BoughtItems")

    def __repr__(self):
        s = "<match_id={0}, region={1}, created_on={2}, duration={3}>"
        return s.format(
            self.match_id, self.region, self.created_on, self.duration)


class Champion(Base):
    __tablename__ = 'champions'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.match_id'))
    participant_id = Column(Integer)
    champion_key = Column(String)
    role = Column(String)
    lane = Column(String)

    def __repr__(self):
        s = "<id={0}, match_id={1}, participant_id={2}, champion_key={3},\
role={4}, lane={5}>"
        return s.format(self.id, self.match_id, self.participant_id,
                        self.champion_key, self.role, self.lane)


class BoughtItems(Base):
    __tablename__ = 'bought_items'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.match_id'))
    item_id = Column(Integer)
    participant_id = Column(Integer)
    timestamp = Column(Integer)

    def __repr__(self):
        s = "<id={0}, match_id={1}, item_id={2} participant_id={3},\
timestamp={4}>"
        return s.format(self.id, self.match_id, self.item_id,
                        self.participant_id, self.timestamp)


def match_loader(matches):
    matches = [match for match in matches if "matchId" in match]
    session = Session()
    new_matches = []
    new_participants = []
    items_bought = []

    for match in matches:
        new_matches.append(Match(
            match_id=match["matchId"],
            region=match["region"],
            created_on=datetime.utcfromtimestamp(
                int(match["matchCreation"] / 1000)),
            duration=timedelta(seconds=match["matchDuration"])
        ))
        for participant in match["participants"]:
            new_participants.append({
                "match_id": match["matchId"],
                "participant_id": participant["participantId"],
                "champion_key": champion_key_from_id(
                    participant["championId"]),
                "role": participant["timeline"]["role"],
                "lane": participant["timeline"]["lane"],
            })
        for item in get_items_bought(match):
            items_bought.append({
                'item_id': item["itemId"],
                'match_id': match["matchId"],
                'participant_id': item["participantId"],
                'timestamp': item["timestamp"]
            })

    session.add_all(new_matches)
    session.commit()
    conn = engine.connect()
    conn.execute(Champion.__table__.insert(), new_participants)
    conn.execute(BoughtItems.__table__.insert(), items_bought)
    conn.close()

champions = riot_api.get_champions()


def champion_keys():
    keys = []
    for champion_id in champions["data"]:
        keys.append(champions["data"][str(champion_id)]["key"])
    return sorted(keys)


def get_items_bought(match):
    if "timeline" not in match:
        return []
    frames = match["timeline"]["frames"]
    events_lists = [
        frame['events'] for frame in frames if "events" in frame
    ]
    events = [
        event for lists in events_lists for event in lists
        if event["eventType"] == "ITEM_PURCHASED"
    ]
    return events


def champion_key_from_id(champion_id):
    return champions["data"][str(champion_id)]["key"]

items = riot_api.get_items()


def item_name_from_id(item_id):
    return items["data"][str(item_id)]["name"]


def item_depth(item_id):
    if "depth" in items["data"][str(item_id)]:
        return items["data"][str(item_id)]["depth"]
    else:
        return 1


def is_final_item(item_id):
    return "into" not in items["data"][str(item_id)]


class ItemTags:
    offensive = {
        "CriticalStrike",
        "SpellDamage",
        "Damage",
        "AttackSpeed",
        "LifeSteal"
    }
    defensive = {
        "Armor",
        "Health",
        "HealthRegen",
        "SpellBlock"
    }
    consumable = {
        "Consumable"
    }


def get_item_set(tag_set):
    s = set()
    tags = tag_set
    for itemKey in items["data"]:
        item = items["data"][itemKey]
        if "tags" in item:
            if not tags.isdisjoint(set(item["tags"])):
                s.add(item["id"])

    return s


def create_db_from_cache():
    with open('matches.cache', 'rb') as f:
        matches = pickle.load(f)

    Base.metadata.create_all(engine)
    match_loader(matches)

if __name__ == "__main__":
    create_db_from_cache()
    print(champion_keys())
