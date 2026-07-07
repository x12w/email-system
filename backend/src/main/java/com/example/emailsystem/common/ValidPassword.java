package com.example.emailsystem.common;

import jakarta.validation.Constraint;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import jakarta.validation.Payload;
import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Validates that a password meets minimum security requirements:
 * at least 8 characters, contains both letters and digits.
 */
@Documented
@Constraint(validatedBy = ValidPassword.PasswordValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidPassword {
    String message() default "密码至少8位，需包含字母和数字";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};

    class PasswordValidator implements ConstraintValidator<ValidPassword, String> {
        private static final int MIN_LENGTH = 8;

        @Override
        public boolean isValid(String value, ConstraintValidatorContext context) {
            if (value == null || value.isBlank()) {
                return false;
            }
            if (value.length() < MIN_LENGTH) {
                return false;
            }
            boolean hasLetter = value.chars().anyMatch(Character::isLetter);
            boolean hasDigit = value.chars().anyMatch(Character::isDigit);
            return hasLetter && hasDigit;
        }
    }
}
