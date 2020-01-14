GENERATED_FILES=councilmatic_core_event.csv councilmatic_core_person.csv

all : $(GENERATED_FILES)

clean :
	rm $(GENERATED_FILES) || :

councilmatic_core_event.csv :
	ssh ubuntu@boardagendas.metro.net " \
	    psql -U postgres -d lametro -c \" \
		    COPY ( \
			    SELECT name, start_time, slug \
			    FROM councilmatic_core_event \
		    ) TO STDOUT WITH CSV HEADER\"" > $@

councilmatic_core_person.csv :
	ssh ubuntu@boardagendas.metro.net " \
	    psql -U postgres -d lametro -c \" \
		    COPY ( \
			    SELECT name, slug \
			    FROM councilmatic_core_person \
		    ) TO STDOUT WITH CSV HEADER\"" > $@
