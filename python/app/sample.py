from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
import json
import redis
import logging
from string import Template

# App
application = Flask(__name__)

# connect to MongoDB
mongoClient = MongoClient('mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] +
                          '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_AUTHDB'])
db = mongoClient[os.environ['MONGODB_DATABASE']]

# connect to Redis
redisClient = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=os.environ.get(
    "REDIS_PORT", 6379), db=os.environ.get("REDIS_DB", 0))


@application.route('/gen')
def generate_data():
    my = {
        "count": 2,
        "score": 33,
        "posA": {

            "correctAnsA": "A",
            "guessA": "C"
        },
        "posB": {

            "correctAnsB": "B",
            "guessB": "A"
        },
        "posC": {

            "correctAnsC": "A",
            "guessC": "A"
        },
        "posD": {

            "correctAnsD": "C",
            "guessD": "A"
        },
        "status": "true"
    }
    db.game.insert_one(my)
    doc = db.game.find_one()
    doc.pop("_id")
    body = json.dumps(doc, indent=4)
    return body


def insert_question(a: str, b: str, c: str, d: str):
    data = {
        "count": 0,
        "score": 0,
        "posA": {

            "correctAnsA": a,
            "guessA": ""
        },
        "posB": {

            "correctAnsB": b,
            "guessB": ""
        },
        "posC": {

            "correctAnsC": c,
            "guessC": ""
        },
        "posD": {

            "correctAnsD": d,
            "guessD": ""
        },
        "status": "false"
    }
    db.game.insert_one(data)
    # return "/?active=playing"


def update_guess(a, b, c, d):
    latest = db.game.find_one({"status": "false"})
    if (
        a == latest['posA']['correctAnsA']
        and b == latest['posB']['correctAnsB']
        and c == latest['posC']['correctAnsC']
        and d == latest['posD']['correctAnsD']
    ):
        score = 400 - latest['count']*4
        update_status = {"$set": {
            "count": latest['count'],
            "score": score,
            "status": "true"
        }}
        db.game.update_one(latest, update_status)
        latest['score'] = score

    update_data = {"$set":
                   {
                       "count": latest['count'] + 1,
                       "posA": {
                           "correctAnsA": latest['posA']['correctAnsA'],
                           "guessA": a
                       },
                       "posB": {
                           "correctAnsB": latest['posB']['correctAnsB'],
                           "guessB": b
                       },
                       "posC": {
                           "correctAnsC": latest['posC']['correctAnsC'],
                           "guessC": c
                       },
                       "posD": {
                           "correctAnsD": latest['posD']['correctAnsD'],
                           "guessD": d
                       }
                   }
                   }
    db.game.update_one(latest, update_data)
    return latest['count'] + 1, latest['score']


@application.route('/', methods=['GET', 'POST'])
def index():

    latest = db.game.find_one({"status": "false"})
    if not latest:
        latest = db.game.find_one()

    with open('index.html', 'r') as f:
        html = f.read()

    count, score = 0, 0
    if request.method == 'POST':
        a = request.form.get("posA")
        b = request.form.get("posB")
        c = request.form.get("posC")
        d = request.form.get("posD")

        if request.args.get('action') == 'setting':
            insert_question(a, b, c, d)
            latest = db.game.find_one({"status": "false"})

        if request.args.get('action') == 'playing' or request.args.get('action') == 'gameover':
            count, score = update_guess(a, b, c, d)

    html = Template(html).safe_substitute(
        count=count,
        score=score,
        correctAnsA=latest['posA']['correctAnsA'] if latest['posA']['correctAnsA'] else "Z",
        correctAnsB=latest['posB']['correctAnsB'] if latest['posB']['correctAnsB'] else "Z",
        correctAnsC=latest['posC']['correctAnsC'] if latest['posC']['correctAnsC'] else "Z",
        correctAnsD=latest['posD']['correctAnsD'] if latest['posD']['correctAnsD'] else "Z"
    )
    return html


@application.route('/sample')
def sample():
    doc = db.game.find_one({"status": "false"})
    # doc = db.game.find_one()
    doc.pop("_id")
    # return jsonify(doc)
    body = '<div style="text-align:center;">'
    body += '<h1>Python</h1>'
    body += '<p>'
    body += '<a target="_blank" href="https://flask.palletsprojects.com/en/1.1.x/quickstart/">Flask v1.1.x Quickstart</a>'
    body += ' | '
    body += '<a target="_blank" href="https://pymongo.readthedocs.io/en/stable/tutorial.html">PyMongo v3.11.2 Tutorial</a>'
    body += ' | '
    body += '<a target="_blank" href="https://github.com/andymccurdy/redis-py">redis-py v3.5.3 Git</a>'
    body += '</p>'
    body += '</div>'
    body += '<h1>MongoDB</h1>'
    body += '<pre>'
    body += json.dumps(doc, indent=4)
    body += '</pre>'
    res = redisClient.set('Hello', 'World')
    if res == True:
        # Display MongoDB & Redis message.
        body += '<h1>Redis</h1>'
        body += 'Get Hello => '+redisClient.get('Hello').decode("utf-8")
    return body


if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("FLASK_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("FLASK_PORT", 5000)
    application.run(host='0.0.0.0', port=ENVIRONMENT_PORT,
                    debug=ENVIRONMENT_DEBUG)
