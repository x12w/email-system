package com.example.emailsystem;

import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.service.impl.MailMessageServiceImpl;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class MailMessageServiceTest {

    // 临时改成手动 new 出来，不走 Spring 和数据库，只验证我们的 if 校验逻辑
    private final MailMessageServiceImpl mailMessageService = new MailMessageServiceImpl();

    @Test
    public void testReceiveAndProcessEmailMissingParam() {
        // 测试异常场景（故意漏掉 fromAddress）
        MailMessage badMsg = new MailMessage();
        badMsg.setUserId(1L);
        badMsg.setAccountId(1L);

        // 验证系统是否会如期抛出我们写好的 IllegalArgumentException 异常
        assertThrows(IllegalArgumentException.class, () -> {
            mailMessageService.receiveAndProcessEmail(badMsg);
        });
    }
}