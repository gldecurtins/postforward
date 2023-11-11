FROM python:latest

RUN apt update && apt upgrade
RUN apt install -y git cmake
RUN git clone https://github.com/roehling/postsrsd.git /usr/src/postsrsd

WORKDIR /usr/src/postsrsd
RUN mkdir _build

WORKDIR /usr/src/postsrsd/_build
RUN cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local
RUN make -j
RUN make install
RUN cp /usr/src/postsrsd/doc/postsrsd.conf /usr/local/etc/postsrsd.conf
RUN sed -i 's/unprivileged-user = "nobody"/unprivileged-user = ""/g' /usr/local/etc/postsrsd.conf
RUN sed -i 's/chroot-dir = "\/usr\/local\/var\/lib\/postsrsd"/chroot-dir = ""/g' /usr/local/etc/postsrsd.conf
RUN sed -i 's/debug = off/debug = on/g' /usr/local/etc/postsrsd.conf

VOLUME ["/var/spool/postfix"]

WORKDIR /usr/src

COPY entrypoint.sh /usr/local/bin/
CMD ["entrypoint.sh", "postsrsd"]
