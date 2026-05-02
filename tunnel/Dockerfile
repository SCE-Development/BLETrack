FROM alpine:latest

RUN apk add --no-cache openssh-client bash

COPY tun.sh /tun.sh
RUN chmod +x /tun.sh

CMD ["/tun.sh"]
