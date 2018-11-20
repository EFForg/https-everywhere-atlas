FROM python:2.7
MAINTAINER William Budington "bill@eff.org"
WORKDIR /opt

COPY requirements.txt /opt/
RUN pip install -r requirements.txt
RUN mkdir output

RUN git config --global user.email "bill@eff.org"
RUN git config --global user.name "William Budington"

COPY atlas.py /opt/
COPY clone-https-everywhere.sh /opt/
COPY graphics  /opt/
COPY output /opt/
COPY templates /opt/

RUN ./clone-https-everywhere.sh https://github.com/efforg/https-everywhere.git master release
VOLUME /opt/https-everywhere/

CMD ['./atlas.py']
