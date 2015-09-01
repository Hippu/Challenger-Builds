Challenger builds
=================

A tool for automatically building item sets for League of Legends
based on the items used by the top tier of players

Requires Python 3

How it works
-----------
The program works by first getting all the matchIds from the matches that
have been recently played by players currently in Challenger

It then downloads the timeline data of these matches using the Match api from
Riot and tallies up all the items purchased there and adds them to a sqlite3
database.

The item sets are then created based on average amount of purchases per game.
Items in the sets are categorized based on whether they are offensive, defensive
starter or consumable items. The items are also sorted by their popularity.
To make the cut item has to be purchased at least in 3 % of the games.

Consumable items show how many times they have been bought by average in a game.

How to use
----------
First you need to add the Riot api key to a file called 'api_key'
the file should only contain the api key and nothing else. The filename must be
in lowercase.

Run generate.py with the number of days as the argument and the
resulting file will be put in the /target folder

The resulting files can then be uploaded or copied to a web server.

Examples
-------
    python generate.py 3

This will create the item sets based on challenger games from the
last three days.

    python generate.py --no-download 2

Generates the item sets from the last two days based on games that have
already been downloaded to the database. Only downloading the static champion
and item data from the Riot Api.

    python generate.py --create-database 3

Using --create-database deletes the existing database of matches and
creates a new one from scratch
