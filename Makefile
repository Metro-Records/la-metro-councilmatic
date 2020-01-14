GENERATED_FILES=councilmatic_core_event.csv councilmatic_core_bill.csv

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

councilmatic_core_bill.csv :
	ssh ubuntu@boardagendas.metro.net " \
	    psql -U postgres -d lametro -c \" \
		    COPY ( \
			    SELECT identifier, slug \
			    FROM councilmatic_core_bill \
		    ) TO STDOUT WITH CSV HEADER\"" > $@
