# Tyler Sverak 12/19/2020
# This program is a helper method, when given a code for a player's smashgg account,
# scrapes their results page and returns a list of dictionaries representing events
# at tournaments.

import requests, re, json
from bs4 import BeautifulSoup


SP_CHARS = ['/', '{', '(', ')', '}', '\"', ',']
FIELDS = {'"id"', '"name"', '"url"', '"locationDisplayName"', '"isOnline"'}
STAND_FIELDS = {'"name"', '"url"', '"placement"', '"outOf"'}

# given a string containing information about a tournament, returns a list of dictionaries each
# representing an event at a tournament
def extract_from_event(event):
    spots = [m.start() for m in re.finditer(',"Entrant:', event)]
    spots.append(len(event) - 1)
    listevent = []
    for spot in spots:
        tourney = {}
        for keyword in STAND_FIELDS:
            index = event.find(keyword, spot)
            index = event.find(':', index)
            if (event[index + 1] == '"'):
                tourney['event_' + keyword[1:-1]] = event[index + 2:event.find('"', index + 3)]
            else:
                end = index + 1
                while (event[end] not in SP_CHARS):
                    end += 1
                tourney[keyword[1:-1]] = event[index + 1:end]
        if str(tourney['placement']).isdigit() :
            nameparts = tourney['event_url'][tourney['event_url'].find("event\\") + 11:tourney['event_url'].find("entrant") - 6].split('-')
            tempname = ''
            for part in nameparts:
                if not part.isdigit() or int(part) == 64:
                    tempname = tempname + ' ' + part[0].upper() + part[1:]
            tourney['event_url'] = tempname.strip()
            listevent.append(tourney)
    return listevent

# given a list of soups, iterates through and pulls events out of each soup
# returns a list of dictionaries each representing an event at a tournament
def from_soup_get_events(soup_menu):
    print("Extracting raw tournament data...")
    tournament_raw = [] # is actually processed events not raw tournaments
    temppage = 1
    for soup in soup_menu:
        results = soup.find_all(lambda tag: tag.name == 'script' and "initialApolloState" in str(tag))
        
        if (results is None):
            print("Error in extraction.")
        else:
            target = str(results)
            # indexes = [m.start() for m in re.finditer('"Tournament:', target)] #to speed this up, you know the first 5 or whatever are bad and the rest are targets
            nextTour = target.find("Tournament:", 0)
            tourney = {}
            while (nextTour >= 0):
                tourney = {}
                tempTour = 0
                if (target[nextTour:nextTour + 25].find('{') != -1):
                    index = 0
                    for keyword in FIELDS:
                        index = target.find(keyword, nextTour)
                        index = target.find(':', index)
                        if (target[index + 1] == '"'):
                            tourney[keyword[1:-1]] = target[index + 2:target.find('"', index + 3)]
                        else:
                            end = index + 1
                            while (target[end] not in SP_CHARS):
                                end += 1
                            tourney[keyword[1:-1]] = target[index + 1:end]
                    tempTour= target.find("Tournament:", index)
                    events = extract_from_event(target[index:tempTour])
                    for e in events:
                        if not str(e['outOf']).isdigit():
                            break
                        temp = tourney.copy()
                        temp.update(e)
                        tournament_raw.append(temp)
                else:
                    tempTour= target.find("Tournament:", nextTour + 15)
                nextTour = tempTour
        temppage += 1
    print("Found " + str(len(tournament_raw)) + " potential events.")
    return tournament_raw


# tries to get the soup from the URL, returns if successful otherwise prints message and returns None
def get_soup(URL):
    page = requests.get(URL)
    if (page.status_code != 200):
        print("The webpage could not be reached.")
        return None
    else:
        return BeautifulSoup(page.content, 'html.parser')

# takes a user ID and collects as many pages exist from their results. Prints progress, returns None if the user ID was invalid
# otherwise returns a list of soups
def soup_collector(user_ID):
    print("Collecting data...")
    res = []
    page_number = 1
    addy = 'https://smash.gg/user/' + user_ID + '/results?page='
    curr_soup = get_soup(addy + str(page_number))
    if (curr_soup is not None):
        while ("No Events" not in str(curr_soup)):
            res.append(curr_soup)
            print("Page " + str(page_number) + " collected.")
            page_number += 1
            curr_soup = get_soup(addy + str(page_number))
        return res
    return None


# run method, calls helper functions in order
def get_player_data(user_ID="35d0bac4"):
    soup_menu = soup_collector(user_ID) # returns list of soup containing 5 tournaments each
    if (soup_menu is None):
        print("Search failed, user ID likely invalid.")
        return None
    else:
        event_data = from_soup_get_events(soup_menu)
        if (event_data is not None and event_data != []):
            print("Scrape successful, tournament data found!")
        return event_data

