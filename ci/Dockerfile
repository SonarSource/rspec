FROM public.ecr.aws/docker/library/python:3.12-slim-bullseye

# Also install NodeJS 20 to run Sonar analysis

RUN apt-get update && \
    apt-get install -y --no-install-recommends jq php-json-schema asciidoctor git curl \
                                               ca-certificates gnupg && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | \
      gpg --dearmor -o /etc/apt/nodesource-keyring.gpg && \
    echo "deb [signed-by=/etc/apt/nodesource-keyring.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
      > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get -y install nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    pip install pipenv


CMD ["bash"]
