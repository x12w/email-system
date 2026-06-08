package com.example.emailsystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.emailsystem.entity.MailIntelligenceResult;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MailIntelligenceResultMapper extends BaseMapper<MailIntelligenceResult> {
    // 不需要写任何代码，基础的增删改查已经全都有了
}