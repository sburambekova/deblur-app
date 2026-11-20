# The site: Vite builds static files, nginx serves them and passes /api and /files on to the
# backend service, so the browser sees one origin and no CORS is needed.
# Built by docker compose from the repository root (see docker-compose.yml).
FROM node:26-alpine AS build

WORKDIR /app

# Dependencies first: this layer is rebuilt only when the lockfile changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.30-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
