package com.example.userservice.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())  // ✅ 禁用 CSRF，避免影响无状态 API
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health").permitAll()  // ✅ 允许所有人访问 /actuator/health
                .anyRequest().authenticated()  // ✅ 其他 API 仍然需要认证
            )
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)); // ✅ 让 API 认证无状态化
        // http
        // .authorizeHttpRequests(auth -> auth
        //     .requestMatchers("/actuator/health").permitAll()  // 允许所有人访问
        //     .anyRequest().authenticated()  // 其他请求仍然需要认证
        // );
        
        return http.build();
    }
}
