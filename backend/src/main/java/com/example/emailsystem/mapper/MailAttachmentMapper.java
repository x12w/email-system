package com.example.emailsystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.emailsystem.entity.MailAttachment;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MailAttachmentMapper extends BaseMapper<MailAttachment> {
}
