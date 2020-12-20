# Tyler Sverak 12/19/2020
# This program takes data scraped using a helper program and graphs it neatly

from tournamentscrape import *
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ACCOUNT_CODE = '35d0bac4' # user ID from smashgg account. this is mine, changing it will change the account scraped.

# takes initial dataframe from get_player_data function and returns it in a cleaner form
def transform_df(df):
    df = df.dropna().copy()
    df[['id', 'placement', 'outOf']] = df[['id', 'placement', 'outOf']].astype(int)
    df['PaaP'] = 1.0 - ((df['placement'] - 1) * 1.0 / df['outOf'])
    order = [] # for order, 0 is most recent
    for x in range(len(df['id'])):
        order.append(x)
    df['order'] = order
    events = df['event_url'].to_list()
    clean_events = []
    for x in range(len(events)):
        event = events[x].lower()
        game = 'Other'
        form = ' Singles'
        gamedict = {'melee':'Melee', 'pm':'Project M', 'project':'Project M', 'brawl':'Brawl', '64':'Smash 64', 'ultimate':'Ultimate', 'wii':'Smash 4'}
        for key in gamedict.keys():
            if (event.find(key) != -1):
                game = gamedict[key]
                break
        if event.find('crew') != -1:
            form = ' Crews'
        elif event.find('double') != -1:
            form = ' Doubles'
        if (game == 'Other'):
            clean_events.append(game)
        else:
            clean_events.append(game + form)
    df['event_url'] = clean_events
    return df


# takes a dataframe and returns a dataframe with the rows containing the event passed
# default event is Melee Singles if no event passed
def filter_by_event(df, event = "Melee Singles"):
    return df[df['event_url'] == event]


# private method
# takes a string and returns the string without the sponsor
def __remove_sponsor(name):
    if '|' in name:
        spot = name.find('|')
        name = name[spot + 1:]
    return name.strip()


# takes a dataframe not filtered by event
# returns a dataframe with the partner's name or team name appended if game is found, otherwise returns empty df
# defaults to looking for Melee Doubles, can look for results in other games if a value is passed
def doubles_partner(df, game = 'Melee'):
    namedf = df[df['event_url'] == game + ' Singles']
    if namedf is not None:
        name = namedf.event_name.mode()[0]
        name = __remove_sponsor(name)
        dubslist = df[df['event_url'] == game + ' Doubles']
        partners = []
        for item in dubslist['event_name']:
            parts = item.split('\\u002F')
            if (len(parts) < 2):
                partners.append("Unknown")
            else:
                for part in parts:
                    part = __remove_sponsor(part)
                    if part != name:
                        partners.append(part)
                        break
        tempdf = dubslist.copy()
        tempdf['partner'] = partners
        counts = tempdf['partner'].value_counts().iloc[:7].index
        tempdf['keep?'] = [False] * len(tempdf['partner'])
        for value in counts:
            tempdf['keep?'] = np.where(tempdf['partner'] == value, True, tempdf['keep?'])
        tempdf['partner'] = np.where(tempdf['keep?'], tempdf['partner'], 'Other')
        return (tempdf['partner'].value_counts(), name)
        
    return (pd.DataFrame(), 'Unknown')


# takes a dataframe and returns a dataframe without online events and a column representing the state/country/etc the event was in
def location_information(df):
    df['online'] = np.where(df['isOnline'] == 'false', 'LAN', 'Online')
    df = df[df.online == 'LAN'].copy()
    df['state'] = df.apply(lambda row: row.locationDisplayName[-2:], axis=1)
    return df


# should be filtered by event before passing df
# takes a dataframe and returns it with a column representing the class the tournament falls into
def categorized_placing_over_time(df):
    df = df.sort_values(by='outOf', ascending=False)
    classes = []
    for row in df.itertuples():
        classes.append( __classify(row.outOf))
    df['class'] = classes
    return df


# private method
# given an integer representing # of participants, returns a string of what class tournament it would be
def __classify(participants):
    # doesnt account for invitaionals or other tournaments where attendance is not reflect of skill level
    size = [12, 24, 48, 100, 500]
    name = ["Smashfest", "Small Local", "Local", "Regional", "Major", "Supermajor"]
    index = 0
    while (index < len(size) and participants >= size[index]):
        index += 1
    return name[index]


# main running method
def run():
    # set up dataframe and basic background
    df = pd.DataFrame(get_player_data(ACCOUNT_CODE))
    df = transform_df(df)
    textcolor = 'yellow'
    fig, axs = plt.subplots(ncols=3, nrows=2, figsize=(14, 8), facecolor='black')
    fig.suptitle('Analysis of _____', fontsize=35, color=textcolor)
    plt.subplots_adjust(hspace = .3, wspace = .4)

    # graph doubles info and create title
    (df1, playername) = doubles_partner(df)
    fig.suptitle('Analysis of ' + playername + "'s Smash Tournaments", fontsize=35, color=textcolor)
    fig.canvas.set_window_title(playername + '_Smash_Tournament_Analysis')
    labels = df1.keys()
    plt.pie(x=df1, autopct="%.1f%%", explode=[0.05]*len(labels), labels=labels, pctdistance=0.5, shadow=True, textprops=dict(color=textcolor))
    plt.title("Doubles Partners", fontsize=14, color=textcolor)

    # graph event info
    sns.set_palette(sns.color_palette("viridis", 5))
    g2 = sns.countplot(y='event_url', data=df, order=df.event_url.value_counts().iloc[:5].index, ax=axs[0, 1])
    g2.set(xlabel="# of Events Entered", ylabel="Events")
    g2.set_yticklabels(g2.get_ymajorticklabels(), fontsize = 6, rotation=30)
    axs[0,1].set_title("Most Entered Events", color=textcolor)
    
    # graph state info
    statecolors = ['#D2996C', '#F8778C', '#3366FF', '#CC3333', '#663300', '#660099', '#003333', '#66FF66', '#006666', '#FFCCFF']
    sns.set_palette(sns.color_palette(statecolors))
    df = filter_by_event(df)
    df2 = location_information(df.copy())
    g3 = sns.countplot(x='state', data=df2, order=df2.state.value_counts().iloc[:10].index, ax=axs[0, 2])
    axs[0, 2].set_title("Number of Tournaments by State", color=textcolor)
    g3.set(xlabel='State/Territory', ylabel="# of Tournaments")

    # graph proportional results
    g4 = sns.regplot(x='outOf', y='placement', data=df, ax=axs[1,0],  scatter_kws={"color": "black"}, line_kws={"color": "red"})
    g4.set_ylim(df['placement'].max() * 1.3, 0)
    g4.set(xlabel="# of Participants", ylabel="Placement")
    axs[1, 0].set_title("Placement with Respect to Proportion", color=textcolor)

    # graphs results by tournament class
    df4 = categorized_placing_over_time(df)
    g5 = sns.lineplot(data=df4, x='order', y='placement', hue='class', ax=axs[1, 1], palette="tab10", linewidth=2.5)
    g5.set_ylim(df['placement'].mean() + .5 * (df['placement'].max() - df['placement'].mean()), 1)
    g5.set_xlim(df['order'].max(), 0)
    sns.despine(ax=axs[1,1])
    g5.set(xlabel="Time (earliest to most recent)", ylabel="Placement")
    g5.legend(title="Classes", shadow = True, facecolor = 'grey', fontsize=5, title_fontsize=7)
    g5.tick_params(bottom=False)
    g5.set_xticks([])
    g5.set_xticks([], minor=True)
    axs[1, 1].set_title("Placement with Respect to Class", color=textcolor)
    
    # graphs online info
    onlinecolors = ['#FF0000', '#000080']
    sns.set_palette(sns.color_palette(onlinecolors))
    df['online'] = np.where(df['isOnline'] == 'false', 'LAN', 'Online')
    g6 = sns.scatterplot(data=df, x="order", y="PaaP", hue='online', ax=axs[0,0])
    g6.legend(title=None, loc='lower right', shadow = True, facecolor = 'grey')
    g6.set_xlim(df['order'].max(), 0)
    g6.set(xlabel="Time (earliest to most recent)", ylabel="% of Competition Outplaced")
    g6.set_xticks([])
    g6.set_xticks([], minor=True)
    axs[0,0].set_title("Comparison of Online and LAN Results", color=textcolor)

    # changes color of graph features
    for graph in axs:
        for ax in graph:
            ax.set_facecolor("yellow") #graph background color
            spinecolor = 'yellow'
            ax.spines['bottom'].set_color(spinecolor)
            ax.spines['top'].set_color(spinecolor)
            ax.xaxis.label.set_color(spinecolor)
            ax.yaxis.label.set_color(spinecolor)
            ax.tick_params(axis='x', colors=spinecolor)
            ax.tick_params(axis='y', colors=spinecolor)

    # display the graphs
    plt.show()

if __name__ == "__main__":
    run()