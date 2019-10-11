FROM python:3.6-slim-stretch
LABEL maintainer "DataMade <info@datamade.us>"

ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y libxml2-dev libxslt1-dev antiword unrtf poppler-utils \
                       pstotext tesseract-ocr flac ffmpeg lame libmad0 \
                       libsox-fmt-mp3 sox libjpeg-dev swig gdal-bin

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install textract==1.6.3

COPY . /app
