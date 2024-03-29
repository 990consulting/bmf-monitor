# This Dockerfile is mainly for development or local runs, but could also 
# be used in production. However, it is not anticipated this will be used,
# since this is primarily going to run in Lambda.
# 
# Test yourself before using in production. Your mileage may vary.

# Pick from a list of tags here: https://hub.docker.com/r/library/python/tags/
FROM python:3.7

MAINTAINER Ben Yanke <ben@yanke.io>

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY main.py /app/

CMD [ "python3", "-u", "/app/main.py" ]
