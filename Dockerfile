FROM node:20-alpine

WORKDIR /app

# Instala dependências primeiro (melhor cache de build)
COPY package.json package-lock.json* ./
RUN npm install --omit=dev

# Copia o restante da aplicação
COPY server.js index.html seed.json ./

EXPOSE 80
CMD ["node", "server.js"]
