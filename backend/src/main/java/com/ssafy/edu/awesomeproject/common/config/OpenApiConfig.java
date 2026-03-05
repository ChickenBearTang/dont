package com.ssafy.edu.awesomeproject.common.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * OpenAPI configuration for Swagger annotations. Use {@code @Tag}, {@code @Operation}, and
 * {@code @ApiResponses} on controllers and methods, and set {@code security = {}} to opt out of the
 * global bearerAuth requirement.
 */
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI openApi() {
        String securitySchemeName = "bearerAuth";

        return new OpenAPI()
                .info(
                        new Info()
                                .title("Chicken Bear Bang Project API")
                                .version("0.0.1-SNAPSHOT")
                                .description("SSAFY 특화 프로젝트 API"))
                .components(
                        new Components()
                                .addSecuritySchemes(
                                        securitySchemeName,
                                        new SecurityScheme()
                                                .type(SecurityScheme.Type.HTTP)
                                                .scheme("bearer")
                                                .bearerFormat("JWT")))
                .addSecurityItem(new SecurityRequirement().addList(securitySchemeName));
    }
}
