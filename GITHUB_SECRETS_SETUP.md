# GitHub Secrets 配置指南

## 📧 QQ邮箱邮件推送配置

### 1. 获取QQ邮箱授权码

1. 登录QQ邮箱网页版：https://mail.qq.com
2. 点击右上角"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"POP3/SMTP服务"或"IMAP/SMTP服务"
5. 点击"生成授权码"，获取16位授权码

### 2. 在GitHub仓库中设置Secrets

1. 进入你的GitHub仓库
2. 点击"Settings"标签页
3. 在左侧菜单中找到"Secrets and variables" → "Actions"
4. 点击"New repository secret"按钮
5. 添加以下三个Secrets：

#### EMAIL_USERNAME
- **Name**: `EMAIL_USERNAME`
- **Value**: `你的QQ邮箱地址` (例如: `844497109@qq.com`)

#### EMAIL_PASSWORD
- **Name**: `EMAIL_PASSWORD`
- **Value**: `QQ邮箱授权码` (16位字符，例如: `ktnuezzpjgvsbbee`)

#### EMAIL_TO
- **Name**: `EMAIL_TO`
- **Value**: `接收邮件的邮箱地址` (例如: `l1396448080@gmail.com`)

### 3. 验证配置

设置完成后，你可以：

1. 进入"Actions"标签页
2. 选择"测试邮件发送"工作流
3. 点击"Run workflow"按钮
4. 查看运行日志，确认配置是否正确

### 4. 常见问题排查

#### 问题1: "Connection unexpectedly closed"
**可能原因**：
- GitHub Secrets未正确设置
- 授权码错误或已过期
- QQ邮箱SMTP服务未开启

**解决方案**：
1. 检查GitHub Secrets是否已设置
2. 重新生成QQ邮箱授权码
3. 确认QQ邮箱已开启SMTP服务

#### 问题2: "SMTPAuthenticationError"
**可能原因**：
- 用户名或密码错误
- 授权码已过期

**解决方案**：
1. 重新生成QQ邮箱授权码
2. 检查邮箱地址是否正确

#### 问题3: "SMTPConnectError"
**可能原因**：
- 网络连接问题
- 防火墙阻止

**解决方案**：
1. 在GitHub Actions云端环境测试（通常网络更稳定）
2. 检查服务器地址和端口配置

### 5. 安全注意事项

⚠️ **重要提醒**：
- 授权码是敏感信息，不要分享给他人
- 更改QQ密码会导致授权码失效，需要重新生成
- 定期更换授权码以提高安全性

### 6. 测试步骤

1. **本地测试**（可选）：
   ```bash
   python test_qq_email.py
   ```

2. **GitHub Actions测试**（推荐）：
   - 在Actions页面运行"测试邮件发送"工作流
   - 查看详细日志输出

3. **完整功能测试**：
   - 运行"run-scheduled-selection"工作流
   - 检查是否收到选股结果邮件

### 7. 配置示例

```yaml
# GitHub Secrets 配置示例
EMAIL_USERNAME: 844497109@qq.com
EMAIL_PASSWORD: ktnuezzpjgvsbbee
EMAIL_TO: l1396448080@gmail.com
```

### 8. 配置文件格式

GitHub Actions会自动创建`user_config.py`文件，格式如下：

```python
USER_CONFIG = {
    'EMAIL_CONFIG': {
        'enabled': True,
        'smtp_server': 'smtp.qq.com',
        'smtp_port': 465,
        'username': '${{ secrets.EMAIL_USERNAME }}',
        'password': '${{ secrets.EMAIL_PASSWORD }}',
        'to_email': '${{ secrets.EMAIL_TO }}',
        'use_tls': False,
        'subject_template': '📈 每日选股推荐 - {date}'
    }
}
```

### 9. 故障排除

如果遇到问题，请按以下顺序检查：

1. ✅ GitHub Secrets是否正确设置
2. ✅ QQ邮箱是否开启SMTP服务
3. ✅ 授权码是否正确且未过期
4. ✅ 网络连接是否正常
5. ✅ 邮箱地址格式是否正确
6. ✅ user_config.py文件格式是否正确

### 10. 联系支持

如果问题仍然存在，请：
1. 查看GitHub Actions的详细日志
2. 运行调试脚本获取更多信息
3. 检查QQ邮箱官方文档
4. 联系技术支持 

from core.config import get_strategy_config
print(get_strategy_config('comprehensive')) 