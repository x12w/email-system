package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.ContactRequest;
import com.example.emailsystem.dto.AppDtos.ContactResponse;
import com.example.emailsystem.entity.Contact;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.ContactService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/contacts")
public class ContactController {
    private final ContactService contactService;

    public ContactController(ContactService contactService) {
        this.contactService = contactService;
    }

    @GetMapping
    public ApiResponse<List<ContactResponse>> list(@RequestParam(required = false) String keyword) {
        return ApiResponse.ok(contactService.listContacts(SecurityUtils.currentUser().id(), keyword)
            .stream().map(this::toResponse).collect(Collectors.toList()));
    }

    @PostMapping
    public ApiResponse<ContactResponse> create(@Valid @RequestBody ContactRequest request) {
        Contact contact = new Contact();
        contact.setName(request.name());
        contact.setEmailAddress(request.emailAddress());
        contact.setPhone(request.phone());
        contact.setRemark(request.remark());
        return ApiResponse.ok(toResponse(contactService.createContact(SecurityUtils.currentUser().id(), contact)));
    }

    @PutMapping("/{id}")
    public ApiResponse<ContactResponse> update(@PathVariable Long id, @Valid @RequestBody ContactRequest request) {
        Contact update = new Contact();
        update.setName(request.name());
        update.setEmailAddress(request.emailAddress());
        update.setPhone(request.phone());
        update.setRemark(request.remark());
        return ApiResponse.ok(toResponse(contactService.updateContact(SecurityUtils.currentUser().id(), id, update)));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        contactService.deleteContact(SecurityUtils.currentUser().id(), id);
        return ApiResponse.ok(null);
    }

    private ContactResponse toResponse(Contact c) {
        return new ContactResponse(c.getId(), c.getName(), c.getEmailAddress(), c.getPhone(), c.getRemark());
    }
}
