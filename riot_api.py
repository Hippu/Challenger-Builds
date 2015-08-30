import requests
import time
import json
from datetime import datetime, timedelta

API_KEY = open('api_key', 'r').readline().rstrip()

riot_api = requests.Session()
riot_api.params.update({"api_key": API_KEY})

beginTime = int((
    datetime.utcfromtimestamp(
        time.time()) - timedelta(days=1)).timestamp()) * 1000

endTime = int(time.time()) * 1000


def get_challenger_summoner_ids():
    challengers = riot_api.get(
        'https://euw.api.pvp.net/api/lol/euw/v2.5/league/challenger',
        params={"type": "RANKED_SOLO_5x5"}
    )
    challengers = sorted(
        challengers.json()["entries"],
        key=lambda player: player['leaguePoints']
    )

    summoner_ids = [p["playerOrTeamId"] for p in challengers]
    return summoner_ids


def get_matches_from_summoner(summoner_id):
    matches = riot_api.get(
        'https://euw.api.pvp.net/api/lol/euw/v2.2/matchlist/by-summoner/' +
        summoner_id,
        params={
            "type": "RANKED_SOLO_5x5",
            "beginTime": beginTime,
            "endTime": endTime,
            "beginIndex": 0,
            "endIndex": 200
        })
    try:
        matches = matches.json()
    except:
        with open('error.log', 'w') as f:
            f.write(matches.text)

    if "matches" in matches:
        return matches["matches"]
    else:
        return []


def get_match_ids_from_challenger(summoner_ids):
    match_ids = set()
    progress_string = "Retrieving matches from summoner {0} out of {1}"

    for index, summoner_id in enumerate(summoner_ids, start=0):
        print(progress_string.format(index, len(summoner_ids)), end='\r')
        for match in get_matches_from_summoner(summoner_id):
            match_ids.add(match["matchId"])
        time.sleep(1.2)

    return match_ids


def get_match(match_id):
    match = riot_api.get(
        'https://euw.api.pvp.net/api/lol/euw/v2.2/match/' + str(match_id),
        params={"includeTimeline": "true"}
    )
    try:
        match = match.json()
    except:
        match = {}
    return match


def get_champions():
    champions = riot_api.get(
        'https://global.api.pvp.net/api/lol/static-data/euw/v1.2/champion',
        params={'dataById': True}
    )
    if champions.status_code != 200:
        print(champions.text)
    else:
        return champions.json()


def get_items():
    items = riot_api.get(
        'https://global.api.pvp.net/api/lol/static-data/euw/v1.2/item',
        params={'itemListData': 'depth,into,tags'}
    )
    return items.json()


def get_matches(match_ids):
    matches = []
    for index, id in enumerate(match_ids):
        print(
            "Retrieving match {0} out {1}".format(index, len(match_ids)),
            end='\r'
        )
        matches.append(get_match(id))
        time.sleep(1.2)
    return matches
