package com.example.emailsystem;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class EmailSystemApplication {

    public static void main(String[] args) {
        SpringApplication.run(EmailSystemApplication.class, args);
    }
}

