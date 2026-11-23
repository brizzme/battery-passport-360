FROM node:22-bookworm-slim AS build
WORKDIR /srv
ENV NEXT_TELEMETRY_DISABLED=1
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-bookworm-slim
WORKDIR /srv
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0
COPY --from=build /srv/.next/standalone ./
COPY --from=build /srv/.next/static ./.next/static
USER node
CMD ["node", "server.js"]
