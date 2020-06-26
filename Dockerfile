FROM debian:buster-slim

RUN apk add --update --no-cache bash curl jq
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      jq \
      php-json-schema && 

CMD ["bash"]
