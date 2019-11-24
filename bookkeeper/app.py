from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import urllib
import pymongo
import config
import random
import requests
import json

app = Flask(__name__)
CORS(app)
db = pymongo.MongoClient(config.MONGODB_URI).get_default_database()

CREDITS = [
    '''
    Photo Credit: Emre Erdogmus<br>
    Shot on iPhone XR<br>
    IG Photography account: <a href="https://www.instagram.com/emresfotos/" target="_blank">@emresfotos</a>
    ''',
    '''
    Photo Credit: Lavanya Kukkemane<br>
    Instagram: @lavanyak814
    ''',
    '''
    Photo Credit: Calvin Harris Belcher
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    '''
]


@app.route("/email/<code>/<name>/<email>")
def add_email(code, name, email):
    lucky = random.randrange(0, len(CREDITS))
    name = urllib.parse.unquote(name)

    doc = db["queue"].find_one({"code": code})

    if doc is None: #course not in db yet
        db["queue"].insert_one({"code": code, "name":name, "emails": [email], "nums": [], "push": []})

    elif email not in doc["emails"]: #email not added already
        doc["emails"].append(email)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})

    else: #already in the db
        msg = '{} was already on the email watchlist for {} {}!'.format(email, code, name)
        return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])

    msg = '{} has been added to the email watchlist for {} {}!</h1></body></html>'.format(email, code, name)
    return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])


@app.route("/sms/<code>/<name>/<num>")
def add_sms(code, name, num):
    lucky = random.randrange(len(CREDITS))
    name = urllib.parse.unquote(name)

    doc = db["queue"].find_one({"code": code})

    if doc is None: #course not in db yet
        db["queue"].insert_one({"code": code, "name":name, "emails": [], "nums": [num], "push": []})

    elif num not in doc["nums"]: #number not added already
        doc["nums"].append(num)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})

    else: #already in the db
        msg = '{} was already on the sms watchlist for {} {}!'.format(num, code, name)
        return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])

    msg = '{} has been added to the sms watchlist for {} {}!'.format(num, code, name)
    return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])


@app.route("/pushnotif/<code>/<name>/<token>")
def add_push_notif(code, name, token):
    lucky = random.randrange(0, len(CREDITS))
    name = urllib.parse.unquote(name)

    doc = db["queue"].find_one({"code": code})

    if doc is None: #course not in db yet
        db["queue"].insert_one({"code": code, "name":name, "emails": [], "nums": [], "push": [token]})

    elif token not in doc["push"]: #token not added already
        doc["push"].append(token)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})

    else: #already in the db
        msg = '{} was already on the push notification watchlist for {} {}!'.format(token, code, name)
        return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])

    msg = '{} has been added to the push notification watchlist for {} {}!</h1></body></html>'.format(token, code, name)
    return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])


@app.route("/testpush/<token>")
def test_push(token):
    fcm = "https://fcm.googleapis.com/fcm/send"
    headers = {"Authorization": config.PUSH_AUTHKEY,
                "Content-Type": "application/json"}
    body = {
        "notification": {
            "title": "AntAlmanac Test Notification",
            "body": "This is a test push notification to make sure you can get it. Click for more details.",
            "click_action": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "icon": "https://www.ics.uci.edu/~rang1/AntAlmanac/img/LogoSquareWhite.png"
        },
        "to": token
        }
    r = requests.post(fcm, data=json.dumps(body), headers=headers)
    return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(0), message='Token push test sent', credits=CREDITS[0])


@app.route("/lookup/<type>/<key>")
def look_up(type,key):
    watchlist = None
    if type == 'email':
        watchlist = [{"code":c['code'], "name": c['name']} for c in db["queue"].find({'emails': key})]
    if type == 'sms':
        watchlist = [{"code":c['code'], "name": c['name']} for c in db["queue"].find({'nums': key})]
    if type == 'push':
        watchlist = [{"code":c['code'], "name": c['name']} for c in db["queue"].find({'push': key})]
    return jsonify(watchlist)


def handler(json_input, context):
    app.run()


if __name__ == '__main__':
    # app.debug = True
    app.run()
