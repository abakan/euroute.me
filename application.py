from time import time
from random import choice
from collections import defaultdict

from flask import Flask, redirect, request, render_template
from flask import json

import numpy as np
import networkx as nx

#from dbhandle import DBHandle

app = Flask(__name__)
#dbh = DBHandle()

app.debug = True

execfile('router.py')

# HTML
@app.route("/")
def index():
    return render_template('index.html')


@app.route("/route")
def route():

    city, country = request.args.get('origin').encode('utf8').split(',')
    origin = destin = CITYMAP[(city.strip(), country.strip())]

    dest = request.args.get('destin')
    if dest:
        dest, _ = dest.encode('utf8').split(',')
        destin = CITYMAP[(dest.strip(), _.strip())]
    else:
        dest = city

    try:
        days = int(request.args.get('days'))
    except ValueError:
        return redirect("/")
    mode = request.args.get('mode', 'transit').upper()[0]

    hours = 4
    routes = get_routes(origin, destin, mode,
                        days, hours)
    return render_template('route.html',
        cities=CITYJSON, routes=json.dumps(routes[:15]),
        links=json.dumps(LINKS[mode, hours]), mode=mode,
        city=city, country=country, dest=dest, days=days,
        origin=origin, destin=destin,
        scores=json.dumps(get_scaled_scores()),
        factoids=json.dumps(FACTOIDS),
        oneway=["false", "true"][origin == destin],
        gmap=bool(int(request.args.get("gmap", 1))))

# JSON
def cities():
    """Return list of cities, e.g ["Berlin, Germany", "Bordeaux, France"]."""

    q = request.args.get('q').split(',')[0]
    sql = ("SELECT city.name, country.name "
           "FROM city JOIN country ON city.countryCode=country.code "
           "WHERE city.name LIKE '{0}%' " #OR Country.name LIKE '{0}%'"
           #"LIMIT 10"
           ).format(q)

    return json.dumps([u'{}, {}'.format(city, country)
                       for city, country in dbh(sql)])


def places():

    city = int(request.args.get('city'))

    cats = [(float(request.args.get('arts')), 'art'),
    (float(request.args.get('history')), 'historic'),
    (float(request.args.get('technical')), 'technical'),
    (float(request.args.get('amusement')), 'amusement'),
    (float(request.args.get('nature')), 'nature'),]

    cats.sort(reverse=True)
    places = {}
    for want, cat in cats:
        if not want:
            break
        places[cat] = dbh("SELECT subcategory, name, url FROM place "
                          "WHERE category='{}' AND cityId={}"
                          .format(cat, city))
    return json.dumps(places)



def reroute():

    origin = int(request.args.get('origin'))
    destin = int(request.args.get('destin'))
    days = int(request.args.get('days'))
    mode = request.args.get('mode').upper()[0]
    hours = int(request.args.get('hours'))
    weights = np.array([float(request.args.get('arts')),
                        float(request.args.get('history')),
                        float(request.args.get('technical')),
                        float(request.args.get('amusement')),
                        float(request.args.get('nature'))])
    routes = get_routes(origin, destin, mode, days, hours, weights)[:15]
    return json.dumps({
        'links': LINKS[mode, hours],
        'scores': get_scaled_scores(weights),
        'routes': routes,
    })


JSON = {
    'cities': cities,
    'reroute': reroute,
    'places': places
}


@app.route("/json/<what>")
def rjson(what):

    return JSON[what]()


if __name__ == "__main__":
    app.run()
    pass