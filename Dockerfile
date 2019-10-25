FROM python:3.7-alpine
LABEL maintainer="William Budington <bill@eff.org>, Alexis Hancock <alexis@eff.org>"

RUN set -ex; \
  apk add --no-cache git; \
  git config --global user.email "bill@eff.org"; \
  git config --global user.name "William Budington"; \
  echo "3 30 * * * root sh -c 'cd /opt && ./atlas.py'" >> /var/spool/cron/crontabs/root

WORKDIR /opt
COPY requirements.txt /opt/

RUN set -ex; \
  \
  apk add --no-cache --virtual .build-deps \
    gcc \
    libxml2-dev \
    libxslt-dev \
    musl-dev \
  ; \
  \
  pip install -r requirements.txt; \
  \
  runDeps="$( \
    scanelf --needed --nobanner --format '%n#p' --recursive /usr/local/lib/python3.7 \
      | tr ',' '\n' \
      | sort -u \
      | awk 'system("[ -e /usr/local/lib/" $1 " ]") == 0 { next } { print "so:" $1 }' \
  )"; \
  apk add --virtual .atlas-rundeps $runDeps; \
  apk del .build-deps

COPY atlas.py /opt/
COPY clone-https-everywhere.sh /opt/
COPY graphics /opt/graphics/
COPY output /opt/output/
COPY templates /opt/templates/
COPY docker/entrypoint.sh /opt/docker/entrypoint.sh

RUN ./clone-https-everywhere.sh https://github.com/efforg/https-everywhere.git master release
VOLUME /opt/https-everywhere/
VOLUME /opt/output/

CMD ["busybox", "crond", "-f", "-l", "0", "-L", "/dev/stdout"]
ENTRYPOINT ["./docker/entrypoint.sh"]
