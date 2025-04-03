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
            .csrf(csrf -> csrf.disable())  // 在API服务中禁用CSRF是常见做法
            .authorizeHttpRequests(auth -> auth
                // 健康检查相关端点
                .requestMatchers("/actuator/health/**").permitAll()  // 允许所有health子路径
                .requestMatchers("/health").permitAll()              // 保留自定义健康检查端点
                
                // 公开端点
                .requestMatchers("/auth/register").permitAll()       // 允许注册端点
                .requestMatchers("/auth/login").permitAll()          // 允许登录端点
                
                // 其他所有请求需要认证
                .anyRequest().authenticated()
            )
            .sessionManagement(session -> 
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            );
        
        return http.build();
    }
}