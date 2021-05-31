FROM gcr.io/language-team/base:latest

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 git

USER sonarsource
