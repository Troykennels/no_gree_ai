# SecureNaija web image. Build context = repo root.
FROM node:22-alpine AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
# npm ci = reproducible install from the lockfile (fails if it drifts).
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production PORT=3000
# Next.js standalone output keeps the runtime image small. Run as the built-in
# non-root `node` user.
COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
