DATABASE_URL=

wagtail_db : legislative_data cms_data

cms_data : db
	docker compose run --rm -e DATABASE_URL=${DATABASE_URL} app python manage.py load_content

legislative_data : db
	docker compose run --rm -e DATABASE_URL=${DATABASE_URL} scrapers
	docker compose run --rm -e DATABASE_URL=${DATABASE_URL} python manage.py refresh_guid
	docker compose run --rm -e DATABASE_URL=${DATABASE_URL} python manage.py update_index

db :
	if [ -z "${DATABASE_URL}" ]; then \
		echo "Please set a value for DATABASE_URL env var" && exit 1; \
	fi
