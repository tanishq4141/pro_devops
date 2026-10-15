# ---- Stage 1: build the React app with Node --------------------------------
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- Stage 2: serve static files with an unprivileged Nginx ----------------
# nginx-unprivileged runs as UID 101 and listens on 8080 (no root needed).
FROM nginxinc/nginx-unprivileged:1.29-alpine
# Pick up the latest Alpine security fixes, then drop back to the unprivileged user.
USER root
RUN apk upgrade --no-cache
# BACKEND_URL is substituted into the template at container start.
ENV BACKEND_URL=http://backend:8000
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
