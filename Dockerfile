FROM nginx:1.29.0-alpine
LABEL \
  org.opencontainers.image.title="nginx config practice" \
  org.opencontainers.image.description="my environment for configuring nginx in my home lab" \
  org.opencontainers.image.version="1.0" \
  org.opencontainers.image.authors="zhabii" 

EXPOSE 80

WORKDIR /usr/share/nginx/html
COPY ./static/ ./
RUN \
  apk add --no-cache curl 
 
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost || exit 1