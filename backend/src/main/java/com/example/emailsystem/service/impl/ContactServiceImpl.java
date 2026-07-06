package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.emailsystem.dto.request.CreateContactRequest;
import com.example.emailsystem.dto.request.UpdateContactRequest;
import com.example.emailsystem.dto.response.ContactResponse;
import com.example.emailsystem.entity.Contact;
import com.example.emailsystem.mapper.ContactMapper;
import com.example.emailsystem.service.ContactService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class ContactServiceImpl implements ContactService {

    private final ContactMapper contactMapper;

    public ContactServiceImpl(ContactMapper contactMapper) {
        this.contactMapper = contactMapper;
    }

    @Override
    public List<ContactResponse> listContacts(Long userId) {
        return contactMapper.selectList(
                new LambdaQueryWrapper<Contact>()
                        .eq(Contact::getUserId, userId)
                        .orderByAsc(Contact::getName)
        ).stream().map(ContactResponse::from).toList();
    }

    @Override
    @Transactional
    public ContactResponse createContact(Long userId, CreateContactRequest req) {
        Contact c = new Contact();
        c.setUserId(userId);
        c.setName(req.name());
        c.setEmailAddress(req.emailAddress());
        c.setPhone(req.phone());
        c.setRemark(req.remark());
        contactMapper.insert(c);
        return ContactResponse.from(c);
    }

    @Override
    @Transactional
    public ContactResponse updateContact(Long userId, Long id, UpdateContactRequest req) {
        Contact c = contactMapper.selectOne(
                new LambdaQueryWrapper<Contact>()
                        .eq(Contact::getId, id)
                        .eq(Contact::getUserId, userId)
        );
        if (c == null) throw new IllegalArgumentException("联系人不存在");
        c.setName(req.name());
        c.setEmailAddress(req.emailAddress());
        c.setPhone(req.phone());
        c.setRemark(req.remark());
        contactMapper.updateById(c);
        return ContactResponse.from(c);
    }

    @Override
    @Transactional
    public void deleteContact(Long userId, Long id) {
        int affected = contactMapper.delete(
                new LambdaQueryWrapper<Contact>()
                        .eq(Contact::getId, id)
                        .eq(Contact::getUserId, userId)
        );
        if (affected == 0) throw new IllegalArgumentException("联系人不存在");
    }
}
