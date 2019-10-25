FROM nginx:alpine
LABEL maintainer="William Budington <bill@eff.org>"

RUN rm /etc/nginx/conf.d/default.conf
COPY atlas.conf /etc/nginx/conf.d/
