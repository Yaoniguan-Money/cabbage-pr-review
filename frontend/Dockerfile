ARG USE_CN_MIRROR=0
FROM node:20-alpine AS build
ARG USE_CN_MIRROR=0
WORKDIR /app

# 国内构建：npm 使用 npmmirror
RUN if [ "$USE_CN_MIRROR" = "1" ]; then \
      npm config set registry https://registry.npmmirror.com; \
    fi

COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
