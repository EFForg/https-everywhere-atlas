FROM python:3.7
LABEL maintainer="William Budington <bill@eff.org>, Alexis Hancock <alexis@eff.org>"
WORKDIR /opt

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
    cron && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* \
    /tmp/* \
    /var/tmp/*

RUN echo "3 30 * * * root bash -c 'cd /opt && ./atlas.py'" >> /etc/crontab
RUN echo >> /etc/crontab

COPY requirements.txt /opt/
RUN pip install -r requirements.txt

RUN git config --global user.email "bill@eff.org"
RUN git config --global user.name "William Budington"

COPY atlas.py /opt/
COPY clone-https-everywhere.sh /opt/
COPY graphics  /opt/graphics/
COPY output /opt/output/
COPY templates /opt/templates/
COPY docker/entrypoint.sh /opt/docker/entrypoint.sh

RUN ./clone-https-everywhere.sh https://github.com/efforg/https-everywhere.git master release
VOLUME /opt/https-everywhere/
VOLUME /opt/output/

CMD ["cron", "-f"]
ENTRYPOINT ["./docker/entrypoint.sh"]
