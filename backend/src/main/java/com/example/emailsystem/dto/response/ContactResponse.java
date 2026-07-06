package com.example.emailsystem.dto.response;

import com.example.emailsystem.entity.Contact;

import java.time.LocalDateTime;

public record ContactResponse(
        Long id,
        String name,
        String emailAddress,
        String phone,
        String remark,
        LocalDateTime createdAt
) {
    public static ContactResponse from(Contact c) {
        return new ContactResponse(c.getId(), c.getName(), c.getEmailAddress(),
                c.getPhone(), c.getRemark(), c.getCreatedAt());
    }
}
