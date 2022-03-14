all : final/boundary.geojson

clean:
	rm -f final/*

final/boundary.geojson : raw/boundary_full_precision.geojson
	ogr2ogr -lco COORDINATE_PRECISION=5 $@ $<

.INTERMEDIATE: raw/boundary_full_precision.geojson	\
                   raw/city_of_la.geojson raw/long_beach.geojson	\
                   raw/southwest_corridor.geojson raw/san_fernando.geojson	\
                   raw/san_gabriel.geojson raw/city_of_la.json \
				   raw/long_beach.json raw/southwest_corridor.json	\
				   raw/san_fernando.json raw/san_gabriel.json

raw/boundary_full_precision.geojson : raw/supervisory_districts.geojson		\
                   raw/city_of_la.geojson raw/long_beach.geojson		\
                   raw/southwest_corridor.geojson raw/san_fernando.geojson	\
                   raw/san_gabriel.geojson
	@printf "\nCombining boundaries...\n"
	python scripts/combine.py $^ | \
            python scripts/add_districts.py > $@

raw/%.geojson : raw/%.json
	@printf "\nConverting raw/%s.json to GeoJSON...\n" "$*"
	cat $< | python scripts/ocd2geojson.py $* > $@

raw/city_of_la.json :
	@printf "\nFetching City of Los Angeles boundaries...\n"
	wget -O $@ https://ocd.datamade.us/boundaries/city-of-la/shape

raw/long_beach.json :
	@printf "\nFetching Long Beach boundaries...\n"
	wget -O $@ https://ocd.datamade.us/boundaries/la-metro-committee-districts/la-metro-committee-district-southeast_long_beach/shape

raw/southwest_corridor.json :
	@printf "\nFetching Southwest Corridor boundaries...\n"
	wget -O $@ https://ocd.datamade.us/boundaries/la-metro-committee-districts/la-metro-committee-district-southwest_corridor/shape

raw/san_fernando.json :
	@printf "\nFetching San Fernando boundaries...\n"
	wget -O $@ https://ocd.datamade.us/boundaries/la-metro-committee-districts/la-metro-committee-district-north_county_san_fernando_valley/shape

raw/san_gabriel.json : 
	@printf "\nFetching San Gabriel boundaries...\n"
	wget -O $@ https://ocd.datamade.us/boundaries/la-metro-committee-districts/la-metro-committee-district-san_gabriel_valley/shape

