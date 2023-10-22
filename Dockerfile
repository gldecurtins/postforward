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

VOLUME ["/var/spool/postfix"]

WORKDIR /usr/src

CMD ["postsrsd"]
