FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 53000

CMD ["npm", "run", "dev"]
