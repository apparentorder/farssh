FROM alpine:3.18 AS build

ENV FARSSH_VERSION 0.1-devel
ENV FARSSH_DATE 2023-08-06

RUN apk add openssh
RUN sed -i "s/AllowTcpForwarding no/AllowTcpForwarding yes/" /etc/ssh/sshd_config

ADD motd /etc/motd
ADD entrypoint /farssh-entrypoint
ADD terminator /farssh-terminator

ENTRYPOINT ["/farssh-entrypoint"]
CMD ["/usr/sbin/sshd", "-e", "-D"]
