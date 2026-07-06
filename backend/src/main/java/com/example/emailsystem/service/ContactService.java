package com.example.emailsystem.service;

import com.example.emailsystem.dto.request.CreateContactRequest;
import com.example.emailsystem.dto.request.UpdateContactRequest;
import com.example.emailsystem.dto.response.ContactResponse;

import java.util.List;

public interface ContactService {
    List<ContactResponse> listContacts(Long userId);
    ContactResponse createContact(Long userId, CreateContactRequest req);
    ContactResponse updateContact(Long userId, Long id, UpdateContactRequest req);
    void deleteContact(Long userId, Long id);
}
