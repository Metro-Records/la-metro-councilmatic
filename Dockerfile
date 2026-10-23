FROM python:3.10-slim
LABEL maintainer "DataMade <info@datamade.us>"

RUN apt-get update && \
    apt-get install -y libpq-dev gcc gdal-bin gnupg && \
    apt-get install -y libxml2-dev libxslt1-dev antiword unrtf poppler-utils postgresql-client \
                       tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 \
                       sox libjpeg-dev swig libpulse-dev curl git ca-certificates && \
    apt-get clean && \
    rm -rf /var/cache/apt/* /var/lib/apt/lists/*

# Heroku's container runtime doesn't honor layer deletions, so CA symlinks that
# ca-certificates removes from /etc/ssl/certs reappear on the dyno. The bundle
# file is regenerated (not deleted), so it comes through clean: point OpenSSL
# clients (curl, git, Python's stdlib ssl) at the bundle and an empty CApath.
RUN mkdir -p /etc/ssl/empty-capath
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_DIR=/etc/ssl/empty-capath

# boto 2 (pulled in by django-councilmatic) ships its own 2015-era CA bundle,
# which includes the distrusted Comodo AAA root. Point it at the system bundle.
RUN printf '[Boto]\nca_certificates_file = /etc/ssl/certs/ca-certificates.crt\n' > /etc/boto.cfg

RUN mkdir /app
WORKDIR /app

RUN curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py --no-cache-dir && \
    rm get-pip.py && \
    pip install --no-cache-dir setuptools "certifi>=2026.10.19"

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV DJANGO_SECRET_KEY 'foobar'
RUN python manage.py collectstatic --no-input

ENTRYPOINT ["/app/docker-entrypoint.sh"]
