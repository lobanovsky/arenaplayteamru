FROM caddy:2.11.4-alpine
RUN setcap -r /usr/bin/caddy
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY index.html /srv/index.html
COPY styles /srv/styles
COPY scripts /srv/scripts
COPY data /srv/data
COPY assets /srv/assets
COPY 404.html /srv/404.html
USER 1000:1000
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/index.html || exit 1

