FROM python:3.6.5
#FROM pypy:3-6

# base
RUN mkdir -p ~/.pip \
    && echo [global] > ~/.pip/pip.conf \
    && echo index-url = https://mirrors.aliyun.com/pypi/simple/ >> ~/.pip/pip.conf \
    && echo extra-index-url = https://pypi.tuna.tsinghua.edu.cn/simple >> ~/.pip/pip.conf \
    && cp -f /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo 'Asia/Shanghai' >/etc/timezone \
    && apt-get update -y \
    && pip install --upgrade pip \
    && apt-get install vim -y

# project
COPY . /opt/project

WORKDIR /opt/project

RUN pip install -r requirements.txt
