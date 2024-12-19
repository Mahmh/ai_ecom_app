FROM node:18-alpine

COPY ./client/ ./app/client/
COPY ./lib/ ./app/lib/

RUN cd ./app/client/ && npm install
RUN npx next telemetry disable

WORKDIR /app/client
EXPOSE 3000
CMD ["npm", "run", "dev"]