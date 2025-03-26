# 使用官方 OpenJDK 17 作为基础镜像
FROM openjdk:17-jdk-slim

# 设置工作目录
WORKDIR /app

# 复制 Maven 构建的 JAR 文件到容器
COPY target/user-service-1.0.0.jar user-service.jar

RUN apt-get update && apt-get install -y curl

# 运行 Spring Boot 应用
ENTRYPOINT ["java", "-jar", "user-service.jar"]
