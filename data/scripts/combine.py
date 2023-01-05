import sys
import json

geojson = {'type': "FeatureCollection",
            'features': []}

for file_name in sys.argv[1:]:
    with open(file_name) as f:
        sub_geojson = json.load(f)
    geojson['features'].extend(sub_geojson['features'])

json.dump(geojson, sys.stdout)
