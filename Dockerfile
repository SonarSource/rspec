FROM debian:buster-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends jq php-json-schema 

CMD ["bash"]
