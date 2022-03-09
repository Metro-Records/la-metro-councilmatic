This directory contains `final/boundary.geojson` and the Makefile and associated scripts used to created it.

The Makefile uses the static file `raw/supervisory_districts.geojson` along with boundaries fetched from
DataMade's OCD (Open Civic Data) endpoint. Fresh OCD files are downloaded to and subsequently removed
from `raw/` each time the Makefile runs.

The Makefile is run using a Docker container separate from the main Docker app that runs the Metro site locally.

To generate new boundaries, first build the Docker app with

`docker-compose build`

Then run

```
docker-compose run --rm app make clean
docker-compose run --rm app make all
```

from this directory.

You'll use the geojson file to load in shapes of districts by running

`docker-compose run --rm app python manage.py import_shapes data/final/boundary.geojson`

from the project's root.
