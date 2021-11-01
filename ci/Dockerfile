FROM python:3.9-slim-buster

RUN pip install pipenv && \
    apt-get update && \
    apt-get install -y --no-install-recommends jq php-json-schema asciidoctor git curl

CMD ["bash"]
