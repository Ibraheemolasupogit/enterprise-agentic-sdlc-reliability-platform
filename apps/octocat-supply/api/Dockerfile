FROM node:24.22.2-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY api/src ./api/src
COPY api/tsconfig.json ./api/tsconfig.json
RUN npm run build:api

FROM node:24.22.2-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c
WORKDIR /app
COPY package.json package-lock.json .npmrc LICENSE ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund && mkdir data && chown node:node data
COPY --from=build --chown=node:node /app/api/dist ./api/dist
USER node
ENV HOST=0.0.0.0 PORT=3000 DB_PATH=data/demo.sqlite
EXPOSE 3000
CMD ["node", "api/dist/server.js"]
