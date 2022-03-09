FROM python:3.8-alpine

LABEL maintainer "DataMade <info@datamade.us>"

# gdal-tools contains ogr2ogr (needed by our scripts)
RUN apk add --no-cache make gdal-tools

RUN mkdir /app

WORKDIR /app

COPY . /app
