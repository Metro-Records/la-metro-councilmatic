import sys
import json

DIVISION = {'la-metro-supervisory-district-1': 'ocd-division/country:us/state:ca/county:los_angeles/council_district:1',
            'la-metro-supervisory-district-2': 'ocd-division/country:us/state:ca/county:los_angeles/council_district:2',
            'la-metro-supervisory-district-3': 'ocd-division/country:us/state:ca/county:los_angeles/council_district:3',
            'la-metro-supervisory-district-4': 'ocd-division/country:us/state:ca/county:los_angeles/council_district:4',
            'la-metro-supervisory-district-5': 'ocd-division/country:us/state:ca/county:los_angeles/council_district:5',
            'Los Angeles': 'ocd-division/country:us/state:ca/place:los_angeles',
             'long_beach': 'ocd-division/country:us/state:ca/county:los_angeles/la_metro_sector:southeast_long_beach',
            'southwest_corridor': 'ocd-division/country:us/state:ca/county:los_angeles/la_metro_sector:southwest_corridor',
            'san_fernando': 'ocd-division/country:us/state:ca/county:los_angeles/la_metro_sector:north_county_san_fernando_valley',
            'san_gabriel': 'ocd-division/country:us/state:ca/county:los_angeles/la_metro_sector:san_gabriel_valley',
             }

geojson = json.load(sys.stdin)

for feature in geojson['features']:
    name = feature['properties']['name']
    feature['properties']['division_id'] = DIVISION[name]

json.dump(geojson, sys.stdout)
