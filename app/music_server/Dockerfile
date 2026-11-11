FROM nginx:1.27-alpine

ENV CORS_ORIGIN="*" \
    CACHE_MAX_AGE="31536000"

COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY make_manifest.sh /docker-entrypoint.d/40-make-manifest.sh
RUN chmod +x /docker-entrypoint.d/40-make-manifest.sh \
    && mkdir -p /usr/share/nginx/html/music

RUN mkdir -p /usr/share/nginx/html/music

EXPOSE 80