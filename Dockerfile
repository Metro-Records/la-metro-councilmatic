FROM python:3.10
LABEL maintainer "DataMade <info@datamade.us>"

# Patch to account for missing Debian Bullseye packages
RUN printf '%s\n' \
        'deb http://archive.debian.org/debian bullseye main' \
        '# https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1147093' \
        'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20260901T022952Z/ bullseye-security main' \
        'deb http://archive.debian.org/debian bullseye-updates main' \
        > /etc/apt/sources.list

RUN apt-get update && \
    apt-get install -y libpq-dev gcc gdal-bin gnupg && \
    apt-get install -y libxml2-dev libxslt1-dev antiword unrtf poppler-utils postgresql-client \
                       tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 \
                       sox libjpeg-dev swig libpulse-dev curl git && \
    apt-get clean && \
    rm -rf /var/cache/apt/* /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install pip==24.0 && \
    pip install --upgrade "setuptools<81" && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV DJANGO_SECRET_KEY 'foobar'
RUN python manage.py collectstatic --no-input

ENTRYPOINT ["/app/docker-entrypoint.sh"]
