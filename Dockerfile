FROM python:3.9-slim-buster

RUN apt-get update && \
    apt-get install -y --no-install-recommends jq php-json-schema asciidoctor
RUN pip install --upgrade pip
RUN pip install pipenv
   
CMD ["bash"]
