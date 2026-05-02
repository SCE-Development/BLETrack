FROM node:20-alpine AS builder

WORKDIR /frontend

COPY package*.json ./
RUN npm ci

COPY . .

ARG REACT_APP_BASE_API_URL=/api
ENV REACT_APP_BASE_API_URL=$REACT_APP_BASE_API_URL

RUN npm run build

FROM nginx:alpine

COPY --from=builder /frontend/build /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
