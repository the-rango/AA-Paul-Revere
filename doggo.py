import pickle
import time
import urllib.parse
import requests
import bs4 as bs

BATCH_SIZE = 8 # Any larger, the field gets cut off and doesn't search for the ones that are cut off
TERM = '2019-92'
WEBSOC = 'https://www.reg.uci.edu/perl/WebSoc?'

def fetch_statuses(targets):
##    statuses = {code:None for code in targets} #is statuses even a word in english? | initialize status values

    lag = 0
    counter = 0
    statuses = {}

    while len(targets[counter*BATCH_SIZE:counter*BATCH_SIZE+BATCH_SIZE]) != 0:
        # get status values for these codes
        codes = set()
        for code in targets[counter*BATCH_SIZE:counter*BATCH_SIZE+BATCH_SIZE]:
            statuses[code] = None
            codes.add(code)
            
        fields = [('YearTerm',TERM),('CourseCodes',', '.join(codes)),('ShowFinals',0),('ShowComments',0),('CancelledCourses','Include')]
        url = WEBSOC + urllib.parse.urlencode(fields)
        # print(url)

        old = time.time()
        first = old

        sauce = requests.get(url)

        #print('\t',time.time()-old)
        old = time.time()

        sp = bs.BeautifulSoup(sauce.content, 'lxml')
    ##        print(sp)

        #print('\t',time.time()-old)
        old = time.time()

        for row in sp.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) > 14 and cells[0].text in statuses:
                code = cells[0].text
                statuses[code] = cells[-1].text

        #print('\t',time.time()-old)
        old = time.time()

        #print()
        lag += (time.time()-first)

        counter += 1

    print('',lag)
    return statuses


while True:
    try:
        l = pickle.load(open('l.p','rb'))
    except:
        print('Doggo did not load properly')
        continue

    s = fetch_statuses(l)

    try:
        pickle.dump(s, open('s.p','wb'))
    except:
        print('Doggo did not dump properly')
        continue

##while True:
##    old = time.time()
##    statuses = pickle.load( open( "s.p", "rb" ) )
##    print(time.time()-old)
