import sys
import re
import json
from math import log
from collections import Counter
from bs4 import BeautifulSoup as htmlParser

# This project is written for Python 2.x
tokenDiction = {}
dfDiction = {} # stores document frequency
urlCount = 0

def argCheck():
    # return false if no enough argument
    if len(sys.argv) < 2:
        return False
    else:
        return True


def checkHtml(f_str):
    return re.match("<(b|strong|h1|h2|h3)>", f_str)


def parseHtml(f_str):
    # return token groups from parsed html
    # reinforce level: b = strong = h3

    if not checkHtml(f_str):
        # doen't contain any html flag
        return [[],[],[]]

    # Utilizes BeautifulSoup to parse
    try:
        result = htmlParser(f_str, "lxml")
    except:
        print "INFO: Broken lxml, ignore."
        return [[],[],[]]

    # Finds all <b> tags
    Btags = [i.string for i in result.findAll('b')]
    BTokens = sum([tokenize(word) for word in Btags],[])

    #Finds all <strong> tags
    StrongTags = [i.string for i in result.findAll('strong')]
    BTokens += sum([tokenize(word) for word in StrongTags], [])

    h1Tags = [i.string for i in result.findAll('h1')]
    h1Tokens = sum([tokenize(word) for word in h1Tags], [])

    h2Tags = [i.string for i in result.findAll('h2')]
    h2Tokens = sum([tokenize(word) for word in h2Tags], [])

    h3Tags = [i.string for i in result.findAll('h3')]
    BTokens += sum([tokenize(word) for word in h3Tags], [])

    return [BTokens, h1Tokens, h2Tokens]


def tokenize(string):
    return re.split("[^0-9a-zA-Z]", string.lower())


def splitBodyTitle(f_str):
    # split a file into title and body
    f_str_delim = f_str.find("<body>")  # index of first <body>

    if 0 <= f_str_delim <= 180:
        title = f_str[:f_str_delim].strip()
        body = f_str[f_str_delim:].strip()
    else:
        # cannot find <body>
        title = ""
        body = f_str

    return (title, body)


def readFile(basePath, doc_id):
    # readfile and update token diction
    global tokenDiction, dfDiction, urlCount

    filename = basePath + "/" + doc_id
    print "DEBUG: Processing " + filename

    try:
        with open(filename, 'r') as fd:
            # read file and split into title, body
            f_str = fd.read()
            splitBodyTitleResult = splitBodyTitle(f_str)
            title = splitBodyTitleResult[0]
            body = splitBodyTitleResult[1]

    except Exception as e:
        print "INFO: Bad file" + doc_id + ", skip..."
        return

    tokenContainer = tokenize(title)
    titleTokenSet = set(tokenContainer)
    tokenContainer.extend(tokenize(body))
    pageTokenCtr = Counter(tokenContainer)

    # parse html using beautiful soup
    parsedHtml = parseHtml(body)
    StrongTokens = parsedHtml[0]
    h1Tokens = parsedHtml[1]
    h2Tokens = parsedHtml[2]

    for token in pageTokenCtr:
        if token == "":
            continue

        # Prepare dictionary
        if token not in tokenDiction:
            tokenDiction[token] = list()

        if token not in dfDiction:
            dfDiction[token] = 1
        else:
            dfDiction[token] += 1

        # tf-idf = log(1+tf)*log(N/df)
        try:
            df = float(dfDiction[token])
            weight = log(1.0 + pageTokenCtr[token], 10) * \
                     log(urlCount / df, 10)
        except Exception as e:
            print "ERROR: Math Exception"
            print e
            weight = 0

        # lw (location weight) in [1,2]
        # tf-idf * lw is used as final weight when searching
        try:
            # if token in title or <h1> set lw to 2, else 1
            if token in titleTokenSet or token in h1Tokens:
                lw = 2.0
            else:
                lw = 1.0

                # <h2> token add 0.6
                if token in h2Tokens:
                    lw += 0.6

                # <b> <strong> <h3> token add 0.3
                if token in StrongTokens:
                    lw += 0.3

        except:
            print "INFO: Broken html, ignore."
            lw = 1.0

        tokenDiction[token].append([doc_id, "{0:.3f}".format(weight), lw])


def countTotalURLs(jsonIndexPath):
    # return the total number of line in the json bookkeeping
    with open(jsonIndexPath) as fd:
        result = sum(1 for _ in fd)
    return result - 2 # deduct empty lines of {}


def readJsonIndex(basePath):
    global urlCount

    # read json index
    jsonIndexPath = basePath + "/" + "bookkeeping.json"
    try:
        urlCount = countTotalURLs(jsonIndexPath)

        with open(jsonIndexPath, 'r') as jsonFd:
            jsonIndex = json.load(jsonFd)

        # get filePath
        if (jsonIndex):
            for doc_id, url in jsonIndex.iteritems():
                readFile(basePath, doc_id)

    except Exception as e:
        print("ERROR: Bad Bookkeeping.json")
        print e


def main():
    # perform argument check.
    # must have exactly one path
    global tokenDiction, urlCount

    if not argCheck():
        print("Invalid argument")
        return

    # open and process file
    try:
        # read json index
        readJsonIndex(sys.argv[1])
    except:
        print("ERROR: Unable to access path. Check your permission")
        return

    with open(sys.argv[1] + "/" + "index.json", 'w') as outputFd:
        json.dump(tokenDiction, outputFd)

    print "Total number of documents:" + str(urlCount)
    print "Total number of tokens:" + str(len(tokenDiction))

if __name__ == "__main__":
    main()