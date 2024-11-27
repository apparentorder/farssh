FROM alpine:3.20 AS build

ENV FARSSH_VERSION=0.5
ENV FARSSH_DATE=2024-11-27

RUN apk add openssh
RUN sed -i "s/AllowTcpForwarding no/AllowTcpForwarding yes/" /etc/ssh/sshd_config

ADD motd /etc/motd
ADD entrypoint /farssh-entrypoint
ADD terminator /farssh-terminator

ENTRYPOINT ["/farssh-entrypoint"]
CMD ["/usr/sbin/sshd", "-e", "-D"]
