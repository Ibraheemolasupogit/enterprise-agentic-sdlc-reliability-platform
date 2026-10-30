FROM node:24.22.2-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY frontend ./frontend
RUN npm run build:web

FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03
COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY LICENSE /usr/share/nginx/html/LICENSE
COPY frontend/nginx.conf frontend/default.conf.template frontend/start.sh /app/
ENV API_PORT=3000
EXPOSE 8080
ENTRYPOINT ["/bin/sh", "/app/start.sh"]
