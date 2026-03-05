FROM alpine:3.23 AS build

ARG FARSSH_DATE=dev
ARG FARSSH_VERSION=dev

ENV FARSSH_VERSION=${FARSSH_VERSION}
ENV FARSSH_DATE=${FARSSH_DATE}

RUN apk add openssh
RUN sed -i "s/AllowTcpForwarding no/AllowTcpForwarding yes/" /etc/ssh/sshd_config

ADD motd /etc/motd
ADD entrypoint /farssh-entrypoint
ADD terminator /farssh-terminator

ENTRYPOINT ["/farssh-entrypoint"]
CMD ["/usr/sbin/sshd", "-e", "-D"]
