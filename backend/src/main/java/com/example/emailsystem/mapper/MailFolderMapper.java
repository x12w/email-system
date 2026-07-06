package com.example.emailsystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.emailsystem.entity.MailFolder;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MailFolderMapper extends BaseMapper<MailFolder> {
}
