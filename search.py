import sys
import json
from flask import Flask
from flask import render_template
from flask import request

http_server = Flask(__name__)

jsonIndex = {}
jsonBookkeeping = {}


def argCheck():
    # return false if no enough argument
    if len(sys.argv) < 2:
        return False
    else:
        return True


def readIndexJson(path):
    global jsonIndex
    try:
        with open(path, 'r') as jsonFd:
            jsonIndex = json.load(jsonFd)

    except Exception as e:
        print("ERROR: Bad index.json")
        print e


def readJsonBookkeepingLst(path):
    global jsonBookkeeping

    try:
        with open(path, 'r') as jsonFd:
            jsonBookkeeping = json.load(jsonFd)

    except Exception as e:
        print("ERROR: Bad Bookkeeping.json")
        print e


def convertDocumentIDtoURL(doc_id):
    global jsonBookkeeping

    return jsonBookkeeping[doc_id]


def intersection(originLst, targetLst):
    result = []

    # generate a list only contain doc ID
    originIDLst = [item[0] for item in originLst]

    for item in targetLst:
        if item[0] in originIDLst:
            result.append(item)

    return result


def generateSingleKeywordResult(keyword):
    # show result for a single keyword (faster)
    global jsonIndex

    result = "<!DOCTYPE html><html><body>"

    try:
        rawPostLstLength = len(jsonIndex[keyword])

        if rawPostLstLength >= 5000:
            result += "For better quality, we only show 5'000 pages with the highest Smart Ranking Score<br>"
            rawPostLst = jsonIndex[keyword][:5000]
        else:
            rawPostLst = jsonIndex[keyword]
    except KeyError:
        return "Cannot find " + keyword
    except Exception as e:
        rawPostLst = jsonIndex[keyword]
        print e

    try:
        # postLst in order of (big->small) tf-idf * location weight
        postLst = sorted(rawPostLst, \
                         key=lambda d: -float(d[1])*float(d[2]))
        result = result + "<h1>" + str(rawPostLstLength) + \
                 " results found for " + keyword + "</h1><br><br>"
    except Exception as e:
        print e
        return "Cannot read index file. Please check if you have permission. "


    for post in postLst:
        docID = post[0]
        tarUrl = convertDocumentIDtoURL(docID)
        result += "<a href=\"http://" + tarUrl + "\">" + tarUrl + "</a><br>"
        result += "Smart Score: " + \
                  "{0:.3f}".format(float(post[1])*float(post[2]))+ "<br><br>"

    result += "</body></html>"
    return result


def generateMultipleKeywordResult(keywords):
    # show result for multiple keyword
    global jsonIndex
    aggregated_postLst = []

    result = "<!DOCTYPE html><html><body>"

    for keyword in keywords:
        try:
            postLst = jsonIndex[keyword]
            if len(aggregated_postLst) == 0:
                aggregated_postLst.extend(postLst)
            else:
                aggregated_postLst = intersection(aggregated_postLst, postLst)

        except KeyError:
            result += "No result for " + keyword + ", we ignored it and look for others.<br>"
            pass # ignore a single keyword
        except Exception as e:
            print e
            return "Cannot read index file. Please check if you have permission. "

    if len(aggregated_postLst) == 0:
        return "Cannot find " + ' '.join(keywords)

    # sort the result
    aggregated_postLst = sorted(aggregated_postLst, \
                            key=lambda d: -float(d[1])*float(d[2]))

    result = result + "<h1>" + str(len(aggregated_postLst)) + \
             " results found</h1><br><br>"

    for post in aggregated_postLst:
        docID = post[0]
        tarUrl = convertDocumentIDtoURL(docID)
        result += "<a href=\"http://" + tarUrl + "\">" + tarUrl + "</a><br>"
        result += "Smart Score: " + \
                  "{0:.3f}".format(float(post[1])*float(post[2]))+ "<br><br>"

    result += "</body></html>"
    return result


@http_server.route('/search.php', methods=['POST'])
def search_result():
    # render search result page
    try:
        keywords_str = request.form['keywords'].lower()
        keywords_lst = keywords_str.split()
    except:
        return "Invalid inquiry. Please try again."

    if len(keywords_lst) <= 0:
        return "Empty inquiry. Please try again."
    elif len(keywords_lst) == 1:
        result = generateSingleKeywordResult(keywords_lst[0])
    else:
        result = generateMultipleKeywordResult(keywords_lst)
    return result


@http_server.route('/')
def index():
    return render_template("index.html")


def main():
    if not argCheck():
        print("Invalid argument")
        return

    # read index json
    basePath = sys.argv[1]
    readIndexJson(basePath + "/" + "index.json")

    # read bookkeeping
    jsonBookkeepingPath = basePath + "/" + "bookkeeping.json"
    readJsonBookkeepingLst(jsonBookkeepingPath)

    # start webserver
    http_server.run()


if __name__ == "__main__":
    main()