package com.example.emailsystem.service;

import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.common.PageResult;
import com.example.emailsystem.dto.AppDtos.AttachmentResponse;
import com.example.emailsystem.dto.AppDtos.ContactRequest;
import com.example.emailsystem.dto.AppDtos.ContactResponse;
import com.example.emailsystem.dto.AppDtos.FolderResponse;
import com.example.emailsystem.dto.AppDtos.MailAccountRequest;
import com.example.emailsystem.dto.AppDtos.MailAccountResponse;
import com.example.emailsystem.dto.AppDtos.MessageDetail;
import com.example.emailsystem.dto.AppDtos.MessageSummary;
import com.example.emailsystem.dto.AppDtos.PushEventResponse;
import com.example.emailsystem.dto.AppDtos.ReadRequest;
import com.example.emailsystem.dto.AppDtos.SendMessageRequest;
import java.nio.charset.StandardCharsets;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class DemoMailboxService {
    private final AtomicLong idGenerator = new AtomicLong(10010);
    private final Map<Long, MailAccountResponse> accounts = new ConcurrentHashMap<>();
    private final Map<Long, FolderResponse> folders = new ConcurrentHashMap<>();
    private final Map<Long, StoredMessage> messages = new ConcurrentHashMap<>();
    private final Map<Long, ContactResponse> contacts = new ConcurrentHashMap<>();
    private final Map<Long, AttachmentResponse> attachments = new ConcurrentHashMap<>();
    private final Map<Long, PushEventResponse> pushEvents = new ConcurrentHashMap<>();

    public DemoMailboxService() {
        MailAccountResponse account = new MailAccountResponse(
            1L, 1L, "admin@example.com", "Admin Mailbox", "localhost", 1025, false,
            "localhost", 1143, false, "admin@example.com", 1, null
        );
        accounts.put(account.id(), account);
        folders.put(1L, new FolderResponse(1L, 1L, "收件箱", "INBOX", "inbox", 2, 3));
        folders.put(2L, new FolderResponse(2L, 1L, "已发送", "Sent", "sent", 0, 1));
        folders.put(3L, new FolderResponse(3L, 1L, "草稿箱", "Drafts", "draft", 0, 1));
        folders.put(4L, new FolderResponse(4L, 1L, "垃圾邮件", "Spam", "spam", 0, 0));

        putMessage(new StoredMessage(
            10001L, 1L, 1L, "security@example.com", "安全团队",
            List.of("admin@example.com"), List.of(), List.of(), "紧急：生产故障审批",
            "html", "<p>生产数据库告警，请在 30 分钟内完成审批。</p>",
            "生产数据库告警，请在 30 分钟内完成审批。", OffsetDateTime.now().minusHours(2),
            false, false, false, 0, "normal", "high", "none"
        ));
        putMessage(new StoredMessage(
            10002L, 1L, 1L, "billing@pay.example.net", "Billing",
            List.of("admin@example.com"), List.of(), List.of(), "Invoice payment verification",
            "html", "<p>Please verify payment at https://192.168.1.5/pay/login</p>",
            "Please verify payment at https://192.168.1.5/pay/login", OffsetDateTime.now().minusHours(8),
            false, true, false, 0, "normal", "normal", "high"
        ));
        putMessage(new StoredMessage(
            10003L, 1L, 1L, "newsletter@example.org", "Weekly News",
            List.of("admin@example.com"), List.of(), List.of(), "本周产品动态",
            "html", "<p>这里是本周的产品动态和团队更新。</p>",
            "这里是本周的产品动态和团队更新。", OffsetDateTime.now().minusDays(1),
            true, false, false, 0, "normal", "normal", "none"
        ));
        putMessage(new StoredMessage(
            10004L, 1L, 2L, "admin@example.com", "Admin",
            List.of("team@example.com"), List.of(), List.of(), "Re: 合同到期提醒",
            "html", "<p>合同到期材料已发出，请查收。</p>",
            "合同到期材料已发出，请查收。", OffsetDateTime.now().minusDays(2),
            true, false, false, 0, "normal", "normal", "none"
        ));
        putMessage(new StoredMessage(
            10005L, 1L, 3L, "admin@example.com", "Admin",
            List.of("finance@example.com"), List.of(), List.of(), "报销材料草稿",
            "html", "<p>本月报销材料待补充附件。</p>",
            "本月报销材料待补充附件。", OffsetDateTime.now().minusHours(4),
            true, false, true, 0, "unknown", "normal", "none"
        ));
        contacts.put(1L, new ContactResponse(1L, "安全团队", "security@example.com", "", "生产告警联系人"));
        contacts.put(2L, new ContactResponse(2L, "财务", "finance@example.com", "", "报销和付款"));
        pushEvents.put(1L, new PushEventResponse(
            1L, 10002L, "security_alert", "发现高风险邮件",
            "Invoice payment verification 包含可疑链接", "high", false, OffsetDateTime.now().minusHours(8)
        ));
    }

    public List<MailAccountResponse> listAccounts(Long userId) {
        return accounts.values().stream().filter(account -> account.userId().equals(userId)).toList();
    }

    public boolean emailAddressExists(String emailAddress) {
        String normalized = normalizeEmail(emailAddress);
        return accounts.values().stream().anyMatch(account -> normalizeEmail(account.emailAddress()).equals(normalized));
    }

    public MailAccountResponse createDefaultMailbox(Long userId, String emailAddress, String displayName) {
        if (emailAddressExists(emailAddress)) {
            throw new BusinessException("MAIL_400", "邮箱地址已被注册");
        }
        long accountId = idGenerator.incrementAndGet();
        String normalizedEmail = normalizeEmail(emailAddress);
        MailAccountResponse account = new MailAccountResponse(
            accountId, userId, normalizedEmail, displayName, "localhost", 1025, false,
            "localhost", 1143, false, normalizedEmail, 1, null
        );
        accounts.put(accountId, account);
        createDefaultFolders(accountId);
        return account;
    }

    public MailAccountResponse createAccount(Long userId, MailAccountRequest request) {
        if (emailAddressExists(request.emailAddress())) {
            throw new BusinessException("MAIL_400", "邮箱地址已被注册");
        }
        long id = idGenerator.incrementAndGet();
        MailAccountResponse account = new MailAccountResponse(
            id, userId, normalizeEmail(request.emailAddress()), request.displayName(), request.smtpHost(), request.smtpPort(),
            request.smtpSsl(), request.imapHost(), request.imapPort(), request.imapSsl(),
            request.authUsername(), 1, null
        );
        accounts.put(id, account);
        createDefaultFolders(id);
        return account;
    }

    public MailAccountResponse updateAccount(Long userId, Long id, MailAccountRequest request) {
        requireAccount(userId, id);
        MailAccountResponse account = new MailAccountResponse(
            id, userId, request.emailAddress(), request.displayName(), request.smtpHost(), request.smtpPort(),
            request.smtpSsl(), request.imapHost(), request.imapPort(), request.imapSsl(),
            request.authUsername(), 1, OffsetDateTime.now()
        );
        accounts.put(id, account);
        return account;
    }

    public void deleteAccount(Long userId, Long id) {
        requireAccount(userId, id);
        accounts.remove(id);
    }

    public List<FolderResponse> listFolders(Long userId) {
        List<Long> accountIds = listAccounts(userId).stream().map(MailAccountResponse::id).toList();
        return folders.values().stream()
            .filter(folder -> accountIds.contains(folder.accountId()))
            .map(this::withComputedCounts)
            .sorted(Comparator.comparing(FolderResponse::id))
            .toList();
    }

    public PageResult<MessageSummary> listMessages(
        Long userId,
        Long folderId,
        String keyword,
        Boolean read,
        String spamLabel,
        String priorityLabel,
        String riskLevel,
        int page,
        int size
    ) {
        List<Long> accountIds = listAccounts(userId).stream().map(MailAccountResponse::id).toList();
        String loweredKeyword = keyword == null ? "" : keyword.toLowerCase(Locale.ROOT);
        List<MessageSummary> filtered = messages.values().stream()
            .filter(message -> accountIds.contains(message.accountId()))
            .filter(message -> folderId == null || message.folderId().equals(folderId))
            .filter(message -> loweredKeyword.isBlank()
                || message.subject().toLowerCase(Locale.ROOT).contains(loweredKeyword)
                || message.preview().toLowerCase(Locale.ROOT).contains(loweredKeyword)
                || message.fromAddress().toLowerCase(Locale.ROOT).contains(loweredKeyword))
            .filter(message -> read == null || message.read() == read)
            .filter(message -> spamLabel == null || spamLabel.equals(message.spamLabel()))
            .filter(message -> priorityLabel == null || priorityLabel.equals(message.priorityLabel()))
            .filter(message -> riskLevel == null || riskLevel.equals(message.riskLevel()))
            .sorted(Comparator.comparing(StoredMessage::receivedAt).reversed())
            .map(StoredMessage::summary)
            .toList();
        int safePage = Math.max(page, 1);
        int safeSize = Math.max(size, 1);
        int from = Math.min((safePage - 1) * safeSize, filtered.size());
        int to = Math.min(from + safeSize, filtered.size());
        return new PageResult<>(filtered.subList(from, to), safePage, safeSize, filtered.size());
    }

    public MessageDetail getMessage(Long userId, Long id) {
        StoredMessage message = requireMessage(userId, id);
        return message.detail();
    }

    public MessageDetail sendMessage(Long userId, SendMessageRequest request, boolean draft) {
        MailAccountResponse account = requireAccount(userId, request.accountId());
        long id = idGenerator.incrementAndGet();
        Long folderId = requireFolder(account.id(), draft ? "draft" : "sent").id();
        String content = request.content() == null ? "" : request.content();
        List<String> to = defaultList(request.to()).stream().map(this::normalizeEmail).toList();
        List<String> cc = defaultList(request.cc()).stream().map(this::normalizeEmail).toList();
        List<String> bcc = defaultList(request.bcc()).stream().map(this::normalizeEmail).toList();
        StoredMessage message = new StoredMessage(
            id, account.id(), folderId, account.emailAddress(), account.displayName(),
            to, cc, bcc,
            request.subject(), request.contentType() == null ? "html" : request.contentType(),
            content, preview(content), OffsetDateTime.now(), true, false, draft,
            request.attachmentIds() == null ? 0 : request.attachmentIds().size(),
            "unknown", "normal", "none"
        );
        putMessage(message);
        if (!draft) {
            deliverToLocalRecipients(account, message, mergeRecipients(to, cc, bcc));
        }
        return message.detail();
    }

    public MessageDetail markRead(Long userId, Long id, ReadRequest request) {
        StoredMessage message = requireMessage(userId, id);
        StoredMessage updated = message.withRead(request.read());
        putMessage(updated);
        return updated.detail();
    }

    public void deleteMessage(Long userId, Long id) {
        requireMessage(userId, id);
        messages.remove(id);
    }

    public List<ContactResponse> listContacts(Long userId, String keyword) {
        String loweredKeyword = keyword == null ? "" : keyword.toLowerCase(Locale.ROOT);
        return contacts.values().stream()
            .filter(contact -> loweredKeyword.isBlank()
                || contact.name().toLowerCase(Locale.ROOT).contains(loweredKeyword)
                || contact.emailAddress().toLowerCase(Locale.ROOT).contains(loweredKeyword))
            .sorted(Comparator.comparing(ContactResponse::name))
            .toList();
    }

    public ContactResponse createContact(Long userId, ContactRequest request) {
        long id = idGenerator.incrementAndGet();
        ContactResponse contact = new ContactResponse(id, request.name(), request.emailAddress(), request.phone(), request.remark());
        contacts.put(id, contact);
        return contact;
    }

    public ContactResponse updateContact(Long userId, Long id, ContactRequest request) {
        requireContact(id);
        ContactResponse contact = new ContactResponse(id, request.name(), request.emailAddress(), request.phone(), request.remark());
        contacts.put(id, contact);
        return contact;
    }

    public void deleteContact(Long userId, Long id) {
        requireContact(id);
        contacts.remove(id);
    }

    public AttachmentResponse uploadAttachment(Long userId, MultipartFile file) {
        long id = idGenerator.incrementAndGet();
        AttachmentResponse attachment = new AttachmentResponse(
            id,
            file.getOriginalFilename() == null ? "attachment" : file.getOriginalFilename(),
            file.getContentType(),
            file.getSize(),
            "local",
            "/api/attachments/" + id + "/download"
        );
        attachments.put(id, attachment);
        return attachment;
    }

    public AttachmentResponse getAttachment(Long id) {
        AttachmentResponse attachment = attachments.get(id);
        if (attachment == null) {
            throw new BusinessException("STORAGE_500", "附件不存在");
        }
        return attachment;
    }

    public byte[] downloadAttachment(Long id) {
        AttachmentResponse attachment = getAttachment(id);
        return ("Demo attachment: " + attachment.originalName()).getBytes(StandardCharsets.UTF_8);
    }

    public void deleteAttachment(Long id) {
        getAttachment(id);
        attachments.remove(id);
    }

    public List<PushEventResponse> listPushEvents() {
        return pushEvents.values().stream()
            .sorted(Comparator.comparing(PushEventResponse::pushedAt).reversed())
            .toList();
    }

    public PushEventResponse markPushEventRead(Long id) {
        PushEventResponse event = pushEvents.get(id);
        if (event == null) {
            throw new BusinessException("INTELLIGENCE_400", "推送事件不存在");
        }
        PushEventResponse updated = new PushEventResponse(
            event.id(), event.messageId(), event.eventType(), event.title(), event.content(),
            event.priority(), true, event.pushedAt()
        );
        pushEvents.put(id, updated);
        return updated;
    }

    public void applyIntelligence(Long messageId, String spamLabel, String priorityLabel, String riskLevel) {
        StoredMessage message = messages.get(messageId);
        if (message != null) {
            putMessage(message.withIntelligence(spamLabel, priorityLabel, riskLevel));
        }
    }

    private void putMessage(StoredMessage message) {
        messages.put(message.id(), message);
    }

    private void createDefaultFolders(Long accountId) {
        createFolder(accountId, "收件箱", "INBOX", "inbox");
        createFolder(accountId, "已发送", "Sent", "sent");
        createFolder(accountId, "草稿箱", "Drafts", "draft");
        createFolder(accountId, "垃圾邮件", "Spam", "spam");
    }

    private void createFolder(Long accountId, String name, String remoteName, String type) {
        long folderId = idGenerator.incrementAndGet();
        folders.put(folderId, new FolderResponse(folderId, accountId, name, remoteName, type, 0, 0));
    }

    private FolderResponse withComputedCounts(FolderResponse folder) {
        List<StoredMessage> folderMessages = messages.values().stream()
            .filter(message -> message.folderId().equals(folder.id()))
            .toList();
        long unread = folderMessages.stream().filter(message -> !message.read()).count();
        return new FolderResponse(
            folder.id(), folder.accountId(), folder.name(), folder.remoteName(), folder.type(),
            Math.toIntExact(unread), folderMessages.size()
        );
    }

    private FolderResponse requireFolder(Long accountId, String type) {
        return folders.values().stream()
            .filter(folder -> folder.accountId().equals(accountId) && folder.type().equals(type))
            .findFirst()
            .orElseThrow(() -> new BusinessException("MAIL_400", "邮箱文件夹不存在"));
    }

    private List<String> mergeRecipients(List<String> to, List<String> cc, List<String> bcc) {
        List<String> recipients = new ArrayList<>();
        recipients.addAll(to);
        recipients.addAll(cc);
        recipients.addAll(bcc);
        return recipients.stream().distinct().toList();
    }

    private void deliverToLocalRecipients(MailAccountResponse senderAccount, StoredMessage sentMessage, List<String> recipients) {
        for (String recipient : recipients) {
            accounts.values().stream()
                .filter(account -> normalizeEmail(account.emailAddress()).equals(normalizeEmail(recipient)))
                .findFirst()
                .ifPresent(account -> {
                    FolderResponse inbox = requireFolder(account.id(), "inbox");
                    StoredMessage received = new StoredMessage(
                        idGenerator.incrementAndGet(),
                        account.id(),
                        inbox.id(),
                        senderAccount.emailAddress(),
                        senderAccount.displayName(),
                        sentMessage.to(),
                        sentMessage.cc(),
                        sentMessage.bcc(),
                        sentMessage.subject(),
                        sentMessage.contentType(),
                        sentMessage.content(),
                        sentMessage.preview(),
                        OffsetDateTime.now(),
                        false,
                        false,
                        false,
                        sentMessage.attachmentCount(),
                        "unknown",
                        "normal",
                        "none"
                    );
                    putMessage(received);
                });
        }
    }

    private MailAccountResponse requireAccount(Long userId, Long id) {
        MailAccountResponse account = accounts.get(id);
        if (account == null || !Objects.equals(account.userId(), userId)) {
            throw new BusinessException("MAIL_400", "邮箱账号不存在");
        }
        return account;
    }

    private StoredMessage requireMessage(Long userId, Long id) {
        StoredMessage message = messages.get(id);
        if (message == null) {
            throw new BusinessException("MAIL_400", "邮件不存在");
        }
        List<Long> accountIds = listAccounts(userId).stream().map(MailAccountResponse::id).toList();
        if (!accountIds.contains(message.accountId())) {
            throw new BusinessException("AUTH_403", "无权限");
        }
        return message;
    }

    private ContactResponse requireContact(Long id) {
        ContactResponse contact = contacts.get(id);
        if (contact == null) {
            throw new BusinessException("MAIL_400", "联系人不存在");
        }
        return contact;
    }

    private List<String> defaultList(List<String> values) {
        return values == null ? new ArrayList<>() : values;
    }

    private String normalizeEmail(String emailAddress) {
        return emailAddress == null ? "" : emailAddress.trim().toLowerCase(Locale.ROOT);
    }

    private String preview(String content) {
        String plain = content.replaceAll("<[^>]+>", "").strip();
        return plain.length() > 120 ? plain.substring(0, 120) : plain;
    }

    private record StoredMessage(
        Long id,
        Long accountId,
        Long folderId,
        String fromAddress,
        String fromName,
        List<String> to,
        List<String> cc,
        List<String> bcc,
        String subject,
        String contentType,
        String content,
        String preview,
        OffsetDateTime receivedAt,
        boolean read,
        boolean starred,
        boolean draft,
        int attachmentCount,
        String spamLabel,
        String priorityLabel,
        String riskLevel
    ) {
        MessageSummary summary() {
            return new MessageSummary(
                id, accountId, folderId, fromAddress, fromName, subject, preview, receivedAt,
                read, starred, draft, attachmentCount, spamLabel, priorityLabel, riskLevel
            );
        }

        MessageDetail detail() {
            return new MessageDetail(
                id, accountId, folderId, fromAddress, fromName, to, cc, bcc, subject, contentType, content,
                preview, receivedAt, receivedAt, read, starred, draft, attachmentCount,
                spamLabel, priorityLabel, riskLevel
            );
        }

        StoredMessage withRead(boolean newRead) {
            return new StoredMessage(
                id, accountId, folderId, fromAddress, fromName, to, cc, bcc, subject, contentType,
                content, preview, receivedAt, newRead, starred, draft, attachmentCount,
                spamLabel, priorityLabel, riskLevel
            );
        }

        StoredMessage withIntelligence(String newSpamLabel, String newPriorityLabel, String newRiskLevel) {
            return new StoredMessage(
                id, accountId, folderId, fromAddress, fromName, to, cc, bcc, subject, contentType,
                content, preview, receivedAt, read, starred, draft, attachmentCount,
                newSpamLabel, newPriorityLabel, newRiskLevel
            );
        }
    }
}
