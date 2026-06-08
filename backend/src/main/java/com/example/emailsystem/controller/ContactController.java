package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.ContactRequest;
import com.example.emailsystem.dto.AppDtos.ContactResponse;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.DemoMailboxService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/contacts")
public class ContactController {
    private final DemoMailboxService mailboxService;

    public ContactController(DemoMailboxService mailboxService) {
        this.mailboxService = mailboxService;
    }

    @GetMapping
    public ApiResponse<List<ContactResponse>> list(@RequestParam(required = false) String keyword) {
        return ApiResponse.ok(mailboxService.listContacts(SecurityUtils.currentUser().id(), keyword));
    }

    @PostMapping
    public ApiResponse<ContactResponse> create(@Valid @RequestBody ContactRequest request) {
        return ApiResponse.ok(mailboxService.createContact(SecurityUtils.currentUser().id(), request));
    }

    @PutMapping("/{id}")
    public ApiResponse<ContactResponse> update(@PathVariable Long id, @Valid @RequestBody ContactRequest request) {
        return ApiResponse.ok(mailboxService.updateContact(SecurityUtils.currentUser().id(), id, request));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        mailboxService.deleteContact(SecurityUtils.currentUser().id(), id);
        return ApiResponse.ok(null);
    }
}
