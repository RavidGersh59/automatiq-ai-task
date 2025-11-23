FROM node:18 AS build
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 3000

CMD sh -c "echo 'Frontend running on http://localhost:3000' && nginx -g 'daemon off;'"
