# Artalk 邮件模板

脚本与三个独立 HTML 位于 scripts/comments/。无需添加 Python 依赖。

生成静态预览（不连接 SMTP；验证码 000000 只是占位）：

```powershell
python scripts/comments/preview-email-templates.py <仓库外的本地预览目录>
python -m unittest discover -s scripts/comments -p test_email_templates.py -v
```

三类模板分别对应 email.mail_tpl、admin_notify.email.mail_tpl、auth.email.verify_tpl。
验证码主题不包含 code；正文按固定版本写明 5 分钟有效。
内容使用原生模板变量，不新增 content_raw、不额外绕过原生转义。
布局以表格与内联样式为主，嵌入样式限制评论图片、代码和长链接。无需远程字体、脚本或品牌图片。

后续部署必须先保存实际活动数据目录、配置、现有模板和前端版本，并校验本机备份：

1. 使用更新后的 backup-artalk.py 创建一致性备份，SHA256SUMS 覆盖 mail-templates 子目录。
2. 将 email_templates.py 及其同级 mail-templates 文件夹上传至私有运维目录。
3. 对持久配置和活动 runtime 配置分别执行下列命令，data_dir 必须来自 Docker 的实际 /data 挂载，不能猜测为 /opt/artalk/data。
4. 仅重载 Artalk，验证路径与模板，再用受控邮箱验收。SMTP 接受不等于收件通过。

```sh
python3 email_templates.py <现有配置文件> <实际活动数据目录>
```

安装器只改模板路径和验证码主题，保留 SMTP 凭据、发送开关及身份设置。
prepare-artalk.py 在新候选初始化时安装模板；configure-auth.py 保留 auth.email 的模板配置。

## 验收与发布门槛

2026-10-27：三个安装测试通过，覆盖配置保留、不完整模板包停止写入以及原生变量白名单。
三类虚构内容静态预览在桌面和移动端可读，长代码及宽图片无横向溢出。预览不连接 SMTP，也不读取真实用户资料。

本次仅提交草稿 PR，不修改生产配置、不发邮件。真实收件、邮件客户端兼容性均未验收；不能以静态浏览器预览或 SMTP 接受代替实际收件。后续须在受控 QA 完成回复、博主通知和验证码邮件收件及链接验证，再部署生产。

回退时恢复旧模板及配置；不使用旧数据库覆盖在线数据。备份中的 mail-templates 子目录必须随配置一起恢复。


## 2026-10-28 隔离验收准备

新建空 QA 数据库，仅包含合成账号和评论，绑定服务器 localhost，经本机 SSH 隧道访问。三个模板已安装；生产配置、OAuth App、账号关联及评论数据未修改。

真实 SMTP 与 GitHub 尚未开放。独立 QA OAuth App 和受控 QQ/Gmail 收件地址等待用户通过服务器私有文件填写；文件权限 0600，凭据不进入仓库。后续须核对 QQ/Gmail 网页端及移动端实际收到三类邮件、链接定位和注册/重置闭环。Outlook 未覆盖。

草稿 PR 保持草稿；不能以已通过的静态预览、安装测试或合成账号登录替代真实收件与授权。
