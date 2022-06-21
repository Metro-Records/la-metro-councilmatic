FROM ubuntu:20.04 as builder

# Clone and build Blackbox
RUN apt-get update && \
    apt-get install -y build-essential git-core && \
    git clone https://github.com/StackExchange/blackbox.git && \
    cd blackbox && \
    make copy-install

FROM python:3.10
LABEL maintainer "DataMade <info@datamade.us>"

# TODO: Figure out how to install pstotext
RUN apt-get update && \
    apt-get install -y libxml2-dev libxslt1-dev antiword unrtf poppler-utils \
                       tesseract-ocr flac ffmpeg lame libmad0 libpq-dev \
                       libsox-fmt-mp3 sox libjpeg-dev swig gdal-bin gnupg && \
    apt-get clean && \
    rm -rf /var/cache/apt/* /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app
COPY councilmatic/settings_deployment.py.example /app/councilmatic/settings_deployment.py

# Copy Blackbox executables from builder stage
COPY --from=builder /usr/local/bin/blackbox* /usr/local/bin/
COPY --from=builder /usr/local/bin/_blackbox* /usr/local/bin/
COPY --from=builder /usr/local/bin/_stack_lib.sh /usr/local/bin/

RUN DATABASE_URL='' python manage.py collectstatic --noinput

ENTRYPOINT ["/app/docker-entrypoint.sh"]
