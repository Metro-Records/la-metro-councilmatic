FROM python:3.10-slim-bullseye
LABEL maintainer "DataMade <info@datamade.us>"

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
    pip install --upgrade setuptools && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV DJANGO_SECRET_KEY 'foobar'
RUN python manage.py collectstatic --no-input

ENTRYPOINT ["/app/docker-entrypoint.sh"]
