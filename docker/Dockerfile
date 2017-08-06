FROM ubuntu:14.04
MAINTAINER zhaoyafei <zhaoyafei0210@gmail.com>

RUN sed -i s/archive.ubuntu.com/mirrors.163.com/g /etc/apt/sources.list 
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
		vim \
        wget \
        unzip \
        curl \
        pkgconf \
        python-dev \
        python-pip \
    rm -rf /var/lib/apt/lists/*
#RUN ln /dev/null /dev/raw1394

RUN pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple -q tornado>= 4.5

WORKDIR /workspace/tornado-file-server
RUN git clone --depth=1 https://github.com/walkoncross/tornado-file-server.git . && \
    ./run.sh