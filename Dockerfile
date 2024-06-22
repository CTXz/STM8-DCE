# Pull latest debian
FROM debian:latest

RUN apt-get update

RUN apt-get install -y \
    wget \
    bzip2 \
    python3 \
    python3-pip

RUN pip3 install colour_runner --break-system-packages

# Download and install SDCC versions from 3.8.0 to 4.4.0
RUN for version in 3.8.0 3.9.0 4.0.0 4.1.0 4.2.0 4.3.0 4.4.0; do \
        wget -O /tmp/sdcc-$version.tar.bz2 "https://sourceforge.net/projects/sdcc/files/sdcc-linux-amd64/$version/sdcc-$version-amd64-unknown-linux2.5.tar.bz2/download" && \
        mkdir -p /opt/sdcc-$version && \
        tar -xvjf /tmp/sdcc-$version.tar.bz2 -C /opt/sdcc-$version --strip-components=1; \
    done

COPY . /root/

RUN pip3 install /root/ --break-system-packages

# Set the entrypoint to /bin/bash
ENTRYPOINT ["/usr/bin/bash", "/root/tests/test.sh", "--ACK"]