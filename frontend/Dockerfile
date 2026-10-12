FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-alpine

WORKDIR /app
COPY --from=builder /app/build ./build
COPY --from=builder /app/package*.json ./
# The runtime only needs node: drop the bundled npm (and its vulnerable
# tar/glob/minimatch/sigstore deps) once production deps are installed.
RUN npm ci --production \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx

EXPOSE 3000
ENV PORT=3000
ENV ORIGIN=http://localhost:3000
CMD ["node", "build/index.js"]
