import pickle
import time
import urllib.parse
import requests
import bs4 as bs

BATCH_SIZE = 8 # Any larger, the field gets cut off and doesn't search for the ones that are cut off
TERM = '2019-92'
WEBSOC = 'https://www.reg.uci.edu/perl/WebSoc?'

def fetch_statuses(statuses):
    # lag = 0                                             # to check code runtime
    counter = 0                                         # just used to take groups of 8
    targets = list(statuses.keys())
    # Updates course statuses in groups of 8 (because websoc can't handle requests of more than 8 courses)
    while len(targets[counter*BATCH_SIZE:counter*BATCH_SIZE+BATCH_SIZE]) != 0:
        # old = time.time()                               # to check code runtime

        # get status values for these codes
        fields = [('YearTerm',TERM),('CourseCodes',', '.join(targets[counter*BATCH_SIZE:counter*BATCH_SIZE+BATCH_SIZE])),('ShowFinals',0),('ShowComments',0),('CancelledCourses','Include')]
        url = WEBSOC + urllib.parse.urlencode(fields)

        sauce = requests.get(url)
        sp = bs.BeautifulSoup(sauce.content, 'lxml')    # parse websoc data

        for row in sp.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) > 14 and cells[0].text in statuses:
                code = cells[0].text
                statuses[code] = cells[-1].text

        # lag += (time.time()-old)                        # to check code runtime
        counter += 1

    #print('',lag)
    return statuses


while True:
    print('run')
    # Load courses to be updated ({code: None})
    try:
        l = pickle.load(open('l.p','rb'))
        # print('loading')
    except:
        print('Doggo did not load properly')
        continue

    print(len(l))

    s = fetch_statuses(l)

    # Dump updated course statuses
    try:
        pickle.dump(s, open('s.p','wb'))
        # print('dumping')
    except:
        print('Doggo did not dump properly')
        continue
