import sys
import json

ocd_map = json.load(sys.stdin)
geojson = {"type": "FeatureCollection", "features": []}

name = sys.argv[1]

try:
    for obj in ocd_map["objects"]:
        feature = {"type": "Feature"}
        feature["geometry"] = obj["shape"]
        feature["properties"] = {"name": obj["name"]}
        geojson["features"].append(feature)
except KeyError:
    feature = {"type": "Feature"}
    feature["geometry"] = ocd_map
    feature["properties"] = {"name": name}
    geojson["features"].append(feature)

json.dump(geojson, sys.stdout)
