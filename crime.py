#!/usr/bin/env python3
import os
import json

from time import sleep
from random import betavariate

import requests

KEY = 'AIzaSyDW3Wvk6xWLlLI6Bfu29DuDaseX-g18_mo'
DIRECTORY = os.path.join('data', 'all_results')

def randomsleep():
    'Sleep between zero and 100 seconds.'
    sleep(10 * betavariate(0.7, 8))

def table(table_id):
    '''
    This would tell us the schema, among other things.
    https://developers.google.com/maps-engine/documentation/reference/v1/tables#resource
    '''

    raise NotImplementedError('This doesn\'t work.')

    url = 'https://www.googleapis.com/mapsengine/v1/tables/%s/' % table_id
    params = {
        'key': KEY,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer':  'http://maps.nyc.gov/crime/',
    }
    r = requests.get(url, headers = headers, params = params)
    return r

def table_features(table_id, select, where = None, maxResults = 1000, pageToken = None):
    url = 'https://www.googleapis.com/mapsengine/v1/tables/%s/features/' % table_id

    params = {
        'key': KEY,
        'version': 'published',
        'maxResults': maxResults,
        'select': select,
    }
    if where:
        params['where'] = where
    if pageToken:
        params['pageToken'] = pageToken

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer':  'http://maps.nyc.gov/crime/',
    }

    r = requests.get(url, headers = headers, params = params)
    return r

def mkpath(pageToken, table_id):
    filename = pageToken if pageToken else '__%s__' % table_id
    return os.path.join(DIRECTORY, filename)

def mkfp(pageToken, table_id, mode = 'xb'):
    return open(mkpath(pageToken, table_id), mode)

def page(table_id, select, pageToken = None):
    '''
    Args: A pageToken or None
    Returns: The next pageToken or None
    '''

    path = mkpath(pageToken, table_id)
    if os.path.exists(path):
        return json.load(open(path))
    else:
        r = table_features(table_id, select, maxResults = 1000, pageToken = pageToken)
        fp = mkfp(pageToken, table_id, mode = 'xb')
        fp.write(r.content)
        fp.close()
        return json.loads(r.text)

def features(table_id, select, startPageToken = None):
    os.makedirs(DIRECTORY, exist_ok = True)

    if startPageToken:
        pageToken = startPageToken
    else:
        print('Loading data for the initial search, without pageToken')
        results = page(table_id, select)
        for result in results.get('features', []):
            yield result
        pageToken = results.get('nextPageToken')

    while pageToken:
        print('Loading data for pageToken', pageToken)
        results = page(table_id, select, pageToken = pageToken)
        for result in results.get('features', []):
            yield result
        pageToken = results.get('nextPageToken')
        randomsleep()

def geojson(table_id, select):
    return {
        'type': 'FeatureCollection',
        'features': list(features(table_id, select)),
    }

def head(table_id, select):
    path = 'head-%s.geojson' % table_id
    if not os.path.exists(path):
        fp = open(path, 'xb')
        r = table_features(table_id, select, maxResults = 10)
        fp.write(r.content)
        fp.close()

def body(table_id, select):
    path = os.path.join('data',table_id + '.geojson')
    if not os.path.exists(path):
        data = geojson(table_id, select)
        json.dump(data, open(path, 'x'))

def main():
    for table_id, select in [
         ('02378420399528461352-11853667273131550346', 'YR,MO,geometry,X,Y,TOT'),
         ('02378420399528461352-17772055697785505571', 'YR,MO,geometry,X,Y,TOT,CR'),
    ]:
        head(table_id, select)
        body(table_id, select)

if __name__ == '__main__':
    main()
