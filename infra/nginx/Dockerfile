FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY http.conf /etc/nginx/templates/http.conf
COPY https.conf /etc/nginx/templates/https.conf
COPY entrypoint-nginx.sh /entrypoint-nginx.sh

RUN chmod +x /entrypoint-nginx.sh

CMD ["sh", "/entrypoint-nginx.sh"]
