package com.example.emailsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.entity.Contact;
import com.example.emailsystem.mapper.ContactMapper;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ContactService {
    private final ContactMapper contactMapper;

    public ContactService(ContactMapper contactMapper) {
        this.contactMapper = contactMapper;
    }

    public List<Contact> listContacts(Long userId, String keyword) {
        QueryWrapper<Contact> wrapper = new QueryWrapper<Contact>().eq("user_id", userId);
        if (keyword != null && !keyword.isBlank()) {
            wrapper.and(w -> w.like("name", keyword).or().like("email_address", keyword));
        }
        return contactMapper.selectList(wrapper.orderByAsc("name"));
    }

    public Contact createContact(Long userId, Contact contact) {
        contact.setUserId(userId);
        contact.setCreatedAt(LocalDateTime.now());
        contact.setUpdatedAt(LocalDateTime.now());
        contactMapper.insert(contact);
        return contact;
    }

    public Contact updateContact(Long userId, Long id, Contact update) {
        Contact contact = contactMapper.selectById(id);
        if (contact == null || !contact.getUserId().equals(userId)) {
            throw new BusinessException("MAIL_400", "联系人不存在");
        }
        contact.setName(update.getName());
        contact.setEmailAddress(update.getEmailAddress());
        contact.setPhone(update.getPhone());
        contact.setRemark(update.getRemark());
        contact.setUpdatedAt(LocalDateTime.now());
        contactMapper.updateById(contact);
        return contact;
    }

    public void deleteContact(Long userId, Long id) {
        Contact contact = contactMapper.selectById(id);
        if (contact == null || !contact.getUserId().equals(userId)) {
            throw new BusinessException("MAIL_400", "联系人不存在");
        }
        contactMapper.deleteById(id);
    }
}
