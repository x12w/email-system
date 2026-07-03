package com.example.emailsystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.emailsystem.entity.MailMessage;
import org.apache.ibatis.annotations.Mapper;

@Mapper // 告诉 Spring Boot 这是一个 MyBatis 的 Mapper 接口，自动注入到容器中
public interface MailMessageMapper extends BaseMapper<MailMessage> {
    // 不需要写任何代码，基础的增删改查已经全都有了
}