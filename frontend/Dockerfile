# 构建阶段
FROM node:18-alpine as build

WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm ci

# 复制所有文件
COPY . .

# 构建生产环境代码
RUN npm run build

# 运行阶段
FROM nginx:alpine

# 复制构建结果到Nginx目录
COPY --from=build /app/build /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]