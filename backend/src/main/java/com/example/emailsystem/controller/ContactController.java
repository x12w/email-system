package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.request.CreateContactRequest;
import com.example.emailsystem.dto.request.UpdateContactRequest;
import com.example.emailsystem.dto.response.ContactResponse;
import com.example.emailsystem.service.ContactService;
import jakarta.validation.Valid;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/contacts")
public class ContactController {

    private final ContactService contactService;

    public ContactController(ContactService contactService) {
        this.contactService = contactService;
    }

    @GetMapping
    public ApiResponse<List<ContactResponse>> list(Authentication auth) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(contactService.listContacts(userId));
    }

    @PostMapping
    public ApiResponse<ContactResponse> create(Authentication auth, @Valid @RequestBody CreateContactRequest req) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(contactService.createContact(userId, req));
    }

    @PutMapping("/{id}")
    public ApiResponse<ContactResponse> update(Authentication auth, @PathVariable Long id, @Valid @RequestBody UpdateContactRequest req) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(contactService.updateContact(userId, id, req));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(Authentication auth, @PathVariable Long id) {
        Long userId = (Long) auth.getPrincipal();
        contactService.deleteContact(userId, id);
        return ApiResponse.ok(null);
    }
}
