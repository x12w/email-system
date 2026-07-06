package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.emailsystem.dto.response.FolderResponse;
import com.example.emailsystem.entity.MailAccount;
import com.example.emailsystem.entity.MailFolder;
import com.example.emailsystem.mapper.MailAccountMapper;
import com.example.emailsystem.mapper.MailFolderMapper;
import com.example.emailsystem.service.FolderService;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class FolderServiceImpl implements FolderService {

    private final MailFolderMapper folderMapper;
    private final MailAccountMapper accountMapper;

    public FolderServiceImpl(MailFolderMapper folderMapper, MailAccountMapper accountMapper) {
        this.folderMapper = folderMapper;
        this.accountMapper = accountMapper;
    }

    @Override
    public List<FolderResponse> listFolders(Long userId) {
        return folderMapper.selectList(
                new LambdaQueryWrapper<MailFolder>()
                        .eq(MailFolder::getUserId, userId)
                        .orderByAsc(MailFolder::getId)
        ).stream().map(FolderResponse::from).toList();
    }

    @Override
    public void syncRemoteFolders(Long userId) {
        // Will be implemented with IMAP folder listing in full sync
        throw new UnsupportedOperationException("远程文件夹同步将在 IMAP 模块完成后可用");
    }
}
