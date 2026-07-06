package com.example.emailsystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.emailsystem.entity.MailRecipient;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MailRecipientMapper extends BaseMapper<MailRecipient> {
}
