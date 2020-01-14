GENERATED_FILES=councilmatic_core_event.csv councilmatic_core_bill.csv

all : $(GENERATED_FILES)

clean :
	rm $(GENERATED_FILES) || :

%.csv :
	ssh ubuntu@boardagendas.metro.net " \
		psql -U postgres -d lametro -c \" \
			copy ( \
				select * \
				from $* \
			) to stdout with csv header\"" > $@

councilmatic_core_bill.csv :
	ssh ubuntu@boardagendas.metro.net " \
		psql -U postgres -d lametro -c \" \
			copy ( \
				select identifier, slug \
				from councilmatic_core_bill \
			) to stdout with csv header\"" > $@
