FROM gradle:8.14.3-jdk21-alpine AS builder
WORKDIR /workspace

COPY gradle gradle
COPY gradlew settings.gradle build.gradle ./
COPY src src

RUN chmod +x gradlew && ./gradlew --no-daemon bootJar

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

COPY --from=builder /workspace/build/libs/*.jar app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
