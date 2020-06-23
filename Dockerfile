FROM alpine

RUN apk add --update --no-cache bash curl jq

CMD ["sh"]
