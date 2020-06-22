# encoding: utf-8
import argparse
import csv
import sys

from workflow import ICON_WEB, Workflow3, web
from workflow.background import is_running

PLAYERS_URL = 'https://d3k2oh6evki4b7.cloudfront.net/short/inc/players_search_list.csv'
PLAYER_CSV_FIELDNAMES = ['id', 'title', 'years', 'active']
PLAYER_REMOVE_FIELDNAMES = ['id', 'title', 'years', 'active']
TEAM_CSV_FIELDNAMES = ['id', 'title', 'years', 'active']

wf = Workflow3(normalization='NFD')


def update_player_data(url):
    r = web.request('GET', url)
    r.save_to_path('players_search_list.csv')
    f = open('players_search_list.csv', 'r')
    csv_reader = csv.DictReader(f, fieldnames=PLAYER_CSV_FIELDNAMES, restkey='can_delete')
    data = []

    for row in csv_reader:
        row.pop('can_delete')
        row['title'] = wf.decode(row['title'])
        data.append(row)

    wf.store_data('players', data)

    return


def update_team_data():
    f = open('teams_search_list.csv', 'r')
    csv_reader = csv.DictReader(f, fieldnames=TEAM_CSV_FIELDNAMES, restkey='can_delete')
    data = []

    for row in csv_reader:
        row.pop('can_delete')
        data.append(row)

    wf.store_data('teams', data)

    return


def generate_url(player_id):
    return 'https://www.baseball-reference.com/players/{}/{}.shtml'.format(player_id[:1], player_id)


def generate_team_url(team_id):
    return 'https://www.baseball-reference.com/teams/{}'.format(team_id)


def search_key_for_post(player):
    """Generate a string search key for a post"""
    elements = [player['id'], player['title'], player['years']]
    return u' '.join(elements)


def main(wf):
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-data')
    parser.add_argument('query', nargs='?', default=None)

    args = parser.parse_args(wf.args)

    if args.update_data:
        return update_player_data(PLAYERS_URL)

    if not wf.cached_data_fresh('player_data', 25) and not is_running('player-update'):
        update_player_data(PLAYERS_URL)

    if not wf.cached_data_fresh('team_data', 2592000):
        update_team_data()

    query = wf.decode(args.query)

    items = wf.stored_data('players')  # Load data from blah

    # If `query` is `None` or an empty string, all items are returned
    items = wf.filter(query, items, key=search_key_for_post)

    # Generate list of results. If `items` is an empty list nothing happens
    for item in items:
        wf.add_item(title=item['title'], subtitle=item['years'], arg=generate_url(item['id']), valid=True,
                    icon=ICON_WEB)

    team_items = wf.stored_data('teams')  # Load data from blah

    # If `query` is `None` or an empty string, all items are returned
    team_items = wf.filter(query, team_items, key=search_key_for_post)

    # Show error if there are no results. Otherwise, Alfred will show
    # its fallback searches (i.e. "Search Google for 'XYZ'")
    if not items and not team_items:
        wf.add_item('No matches')

    # Generate list of results. If `items` is an empty list nothing happens
    for item in team_items:
        wf.add_item(title=item['title'], subtitle=item['years'], arg=generate_team_url(item['id']), valid=True,
                    icon=ICON_WEB)

    wf.send_feedback()

    return 0


if __name__ == u"__main__":
    wf = Workflow3(normalization='NFD')
    sys.exit(wf.run(main))
