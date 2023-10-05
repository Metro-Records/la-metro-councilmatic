all : final/boundary.geojson

clean :
	rm -f final/*

final/boundary.geojson : raw/boundary_full_precision.geojson
	ogr2ogr -lco COORDINATE_PRECISION=5 $@ $<

.INTERMEDIATE: raw/boundary_full_precision.geojson

raw/boundary_full_precision.geojson : raw/supervisory_districts.geojson \
				   raw/committee_districts.geojson \
				   raw/caltrans_district.geojson \
				   raw/los_angeles.geojson
	@printf "\nCombining boundaries...\n"
	python3 scripts/combine.py $^ | \
	python3 scripts/add_districts.py > $@
