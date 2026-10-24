FROM node:22-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund

FROM node:22-alpine
ARG SOURCE_REVISION
LABEL org.opencontainers.image.source="https://github.com/gutocarollo/architecture-system-eng-expert"
LABEL org.opencontainers.image.revision="$SOURCE_REVISION"
ENV NODE_ENV=production PORT=8080
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY --chown=node:node package.json app.js server.js export-manifest.json ./
COPY --chown=node:node public ./public
USER node
EXPOSE 8080
CMD ["node", "server.js"]
