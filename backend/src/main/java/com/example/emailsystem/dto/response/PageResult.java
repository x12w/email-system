package com.example.emailsystem.dto.response;

import java.util.List;

public record PageResult<T>(
        List<T> records,
        long page,
        long size,
        long total
) {
    public static <T> PageResult<T> of(List<T> records, long page, long size, long total) {
        return new PageResult<>(records, page, size, total);
    }
}
