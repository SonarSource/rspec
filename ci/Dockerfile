FROM public.ecr.aws/docker/library/python:3.9-slim-bullseye

RUN apt-get update && \
    apt-get install -y --no-install-recommends jq php-json-schema asciidoctor pipenv git curl libc6 python3-setuptools

CMD ["bash"]
