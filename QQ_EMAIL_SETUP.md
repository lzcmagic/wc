# QQ邮箱SMTP配置说明

## 当前配置
- **发送邮箱**: 844497109@qq.com
- **接收邮箱**: l1396448080@gmail.com
- **授权码**: ktnuezzpjgvsbbee
- **SMTP服务器**: smtp.qq.com
- **端口**: 587 (TLS) 或 465 (SSL)

## 本地测试结果
❌ **连接失败**: 网络环境限制导致连接被重置

## 解决方案

### 1. 检查QQ邮箱设置
1. 登录QQ邮箱网页版
2. 进入"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 确保开启了"POP3/SMTP服务"

### 2. 在GitHub Actions中测试
由于本地网络环境限制，建议在GitHub Actions中测试：

1. 在GitHub仓库设置中添加Secrets：
   - `EMAIL_USERNAME`: 844497109@qq.com
   - `EMAIL_PASSWORD`: ktnuezzpjgvsbbee
   - `EMAIL_TO`: l1396448080@gmail.com

2. 手动触发测试工作流：
   - 进入GitHub仓库的Actions页面
   - 选择"测试邮件发送"工作流
   - 点击"Run workflow"

### 3. 备用方案
如果QQ邮箱仍有问题，可以考虑：
- 使用Gmail邮箱
- 使用其他国内邮箱服务（如163、126等）
- 使用企业邮箱服务

## 测试文件
- `test_qq_email.py`: 本地测试脚本
- `debug_qq_email.py`: 详细调试脚本
- `.github/workflows/test_email.yml`: GitHub Actions测试工作流 