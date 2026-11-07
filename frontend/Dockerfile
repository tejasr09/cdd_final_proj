FROM node:24.14.1-alpine

WORKDIR /app
RUN chown node:node /app
USER node
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

COPY --chown=node:node index.html vite.config.ts tsconfig*.json eslint.config.js .prettierrc.json ./
COPY --chown=node:node src ./src

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
