package com.example.emailsystem.dto.response;

import com.example.emailsystem.entity.MailFolder;

public record FolderResponse(
        Long id,
        Long accountId,
        String name,
        String type,
        Integer unreadCount,
        Integer totalCount
) {
    public static FolderResponse from(MailFolder f) {
        return new FolderResponse(f.getId(), f.getAccountId(), f.getName(), f.getType(),
                f.getUnreadCount(), f.getTotalCount());
    }
}
