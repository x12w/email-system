package com.example.emailsystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.emailsystem.entity.MailPushEvent;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MailPushEventMapper extends BaseMapper<MailPushEvent> {
}
