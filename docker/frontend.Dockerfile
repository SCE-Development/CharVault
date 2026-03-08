FROM node:20-alpine
WORKDIR /src/app

COPY package*.json ./
RUN npm ci

COPY . .

# Build is REQUIRED for "next start"
RUN npm run build

EXPOSE 3000
CMD ["npm","start"]