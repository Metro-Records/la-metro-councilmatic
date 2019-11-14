all : boundary.geojson

boundary.geojson : boundary_full_precision.geojson
	ogr2ogr -lco COORDINATE_PRECISION=5 $@ $<

.INTERMEDIATE: boundary_full_precision.geojson
boundary_full_precision.geojson : supervisory_districts.geojson		\
                   city_of_la.geojson long_beach.geojson		\
                   southwest_corridor.geojson san_fernando.geojson	\
                   san_gabriel.geojson
	python scripts/combine.py $^ | \
            python scripts/add_districts.py > $@

%.geojson : %.json
	cat $< | python scripts/ocd2geojson.py $* > $@

supervisory_districts.json :
	wget -O $@ https://ocd.datamade.us/boundaries/la-metro-supervisory-districts/shape

city_of_la.json :
	wget -O $@ wget -O $@ https://ocd.datamade.us/boundaries/city-of-la/shape

long_beach.json :
	wget -O $@ https://ocd.datamade.us/boundaries/la-metro-committee-districts/la-metro-committee-district-southeast_long_beach/shape

southwest_corridor.json :
	wget -O $@ https://ocd.datamade.us/boundaries/la-metro-committee-districts/la-metro-committee-district-southwest_corridor/shape

san_fernando.json :
	wget -O $@ https://ocd.datamade.us/boundaries/la-metro-committee-districts/la-metro-committee-district-north_county_san_fernando_valley/shape

san_gabriel.json : 
	wget -O $@ https://ocd.datamade.us/boundaries/la-metro-committee-districts/la-metro-committee-district-san_gabriel_valley/shape

