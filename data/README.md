This directory contains a `boundary.geojson` file and the Makefile
used to created it.

You'll use the geojson file to load in shapes of districts with

`python manage.py import_shapes data/boundary.geojson`


You shouldn't need to rerun the Makefile, but keep it for historical
reference.

This Makefile currently depends on pulling data from DataMade's legacy
OCD API. In the future, if boundary changes, we won't put the data
into the that API at all, but will more create an updated
`boundary.geojson` file much more directly.



