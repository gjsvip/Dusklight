# 评论迁移备忘：Twikoo → Artalk

## 状态与边界

2026-10-25 实施备份、恢复演练及候选版本。**生产博客和 Twikoo 尚未切换，未推送 main 或发布生产产物。** 新入口通过 EdgeOne CNAME 接入；源站地址、管理员凭据和邮件配置仅保存在私有运维目录，不写入此公开仓库。

后续头像、样式、GitHub 登录及正式上线计划已获 commit、push 和切换授权。实施分支 `codex/artalk-comment-migration` 基于最新 `origin/main`，原工作区及 `friends.ts` 的既有修改不纳入提交。OAuth 凭据、真实登录、通知收件、回源身份及最终备份验收未完成前，不停写 Twikoo。

## 头像、样式及登录适配进度

- 历史 QQ 头像恢复 419 条；不再使用统一 `d=mp`。评论卡片、下置身份输入栏、大输入区、工具按钮和回复层级对照生产版适配，使用站点轻量材质，无评论区域背景模糊。
- 本机候选预览 `http://127.0.0.1:4324/envelope/#comments`，仅在候选后端增加此预览来源；正式配置不包含预览来源。
- 原生 GitHub 配置工具为 `scripts/comments/configure-auth.py`。用户需在服务器 `/opt/artalk/oauth.private.json`（0600）填写 `client_id`、`client_secret`；工具遇到空值会在修改配置前失败。回调为 `https://artalk.mcxiaochen.top/api/v2/auth/github/callback`，仅启用 GitHub 和匿名评论，沿用随固定镜像提供的官方登录插件。
- 为避免无条件信任访客 IP 头，已生成 `/opt/artalk/origin-auth.private.json`（0600）。EdgeOne 需覆盖回源请求头 `X-Dusklight-Origin-Key` 为文件中的随机值，并让 `/api/v2/*` 绕过缓存。配置验证后才在 Artalk 站点反代启用回源鉴权及真实访客 IP；不修改其他站点的 real-IP 配置。
- 当前 GitHub 凭据尚未填写，原生登录尚未启用，真实 GitHub 授权和 Artalk 通知实际收件未验收。候选公网评论写入继续关闭；后台 `/sidebar/` 已存在，但其登录 POST 仍受候选限制，不能把此状态称为后台已可登录。

- 后端固定 `artalk/artalk-go:2.10.0`，实际部署按 digest 固定为 `sha256:ed51450f3ed744780efd0d796f1ea033063bb11543973439b9c57ed32ac9b78f`，前端 npm 固定 `artalk@2.10.0`。
- 独立 Compose：`/opt/artalk/compose.yml`；候选 SQLite 与配置：`/opt/artalk/data/`；只监听 `127.0.0.1:23366`。
- 候选公网入口仅允许 GET/HEAD/OPTIONS，写入返回 403；候选服务真实邮件关闭。生产邮件配置和随机生成的管理员凭据分别存于 `/opt/artalk/production.private.yml`、`/opt/artalk/admin.private.json`，只允许 root 读取。
- 隔离恢复容器为 `dusklight-mongo-restore`、`dusklight-twikoo-restore`；独立功能测试容器为 `dusklight-artalk-qa`，其测试数据不得作为正式迁移源。验收后仅停止这三个测试容器，保留其数据与日志；候选服务继续运行。

## 历史页面归并决定

规则由 `src/config/comment-paths.json` 提供，迁移脚本和客户端共享；只规范尾斜杠，不重新生成文章 abbrlink。

| 原路径 | 新页面键 | 基线数量与决定 |
| --- | --- | --- |
| `/comments/` | `/envelope/` | 旧留言板 37 条合并 |
| `/envelope`、`/envelope/` | `/envelope/` | 原有 21 条保留 |
| `/posts/p562369c9` | `/envelope/` | 已删除《博客迁移通知》2 条并入，正文增加来源说明；留言板合计 60 条 |
| `/equipment/` | `/devices/` | 设备页 5 条，恢复评论入口 |
| `/log/` | `/timeline/` | 博客日志 1 条，沿用更新日志入口并恢复评论 |
| `/link`、`/link/` | `/link/` | 友链页 125 条合并 |
| `/about`、`/about/` | `/about/` | 关于页 4 条合并 |
| `/categories/` | `/categories/` | 分类索引 1 条，恢复评论入口 |
| `/essay/` | **原键 `/essay/`** | **即刻短文 14 条完整保留，页面后续可能加回；当前不恢复页面、不并入留言板，最新评论暂不展示** |
| 其他文章路径 | 现有 `/posts/<slug>/` | 合并有无尾斜杠的同一文章 |

《博客迁移通知》在旧 `xcBlog` 的 `f3bfeb1` 提交中被主动删除。本次**仅迁移评论，不恢复或重新发布该文章**。旧路径跳转与旧评论 ID 定位同时保留。

## 数据基线、保真与已知差异

基线批次 `20261025-162747-baseline`：552 条评论、311 条回复、19 条待审、1 条置顶、143 赞、1 踩，21 条旧计数记录。转换及 SQLite 导入已逐条核对正文、页面归属、IP/UA、作者、毫秒时间、状态、投票和直接回复目标；完整性检查通过，无孤立回复。最终切换必须重新统计，不把本次数量硬编码为最终数量。

- 551 条正文含 HTML，保持原 HTML 与表情，不转换为纯文本；仅已删通知的两条增加来源说明。
- `ups` 存在时优先，否则回退旧 `like`；`downs` 为点踩，禁止将新旧赞相加。历史投票者身份只保存在私有备份。
- 原始 `avatar`、`ipRegion`、`uid` 以及旧浏览量计数均完整归档。原导出中的 376 个 `avatar` 字段均为空；旧版主要依据头像服务和 QQ 邮箱显示头像。后续用户明确授权恢复历史 QQ 直链（接受 URL 中 QQ 号公开），从私有源数字 QQ 邮箱匹配出 419 条评论，经已核验的 ID 映射生成 `public/comments/historical-avatars.json`。其余评论使用 Gravatar，未注册时使用稳定的 `d=identicon` 图案；QQ 加载失败仅回退一次。主评论和最新评论共用解析逻辑，不新增 QQ 输入识别或昵称查询功能。
- Artalk 按忽略大小写的昵称和邮箱匹配账户，2 条评论的作者显示大小写发生等价归并；原始写法仍完整保存在私有源数据。
- Artalk 将网站地址存为作者账户资料，而非逐条评论字段；基线有 300 条显示链接与原值不同，其中 40 条仅补全 `https://`。用户选择保留原生账户资料，原网址和原始头像字段留在私有备份；后续仅新增上述获授权的历史 QQ 头像展示映射。
- 历史博主标识仅依据原已配置的博主邮箱恢复；管理员通过独立随机凭据创建，不按评论中的 `master` 自动授予权限。旧登录态不迁移。
- `public/comments/legacy-map.json` 只含旧 ID、新页面键、新数字 ID，无正文、昵称、邮箱或 IP。该文件只对应当前试迁移，最终导入后必须重新生成并重新构建前端。

## 备份与恢复

服务器基线：`/opt/backups/dusklight-comments/20261025-162747-baseline/`，目录权限 0700。包含 MongoDB 完整逻辑归档、各集合 JSON、原镜像、容器与镜像元数据、Compose/环境变量、反代及通配证书，以及 SHA256SUMS。基线在生产运行期间生成；它不能替代最终停写备份。

本机已验证备份位于 `D:\Backups\Dusklight\comment-migration\20261025-162747-baseline-verified\20261025-162747-baseline\`，仅本人和 SYSTEM 可访问。原清单 14 项、含恢复证据的完整清单 17 项均逐文件 SHA-256 校验通过；早期不完整下载目录不计作备份成功。服务器恢复证据位于 `/opt/artalk/rehearsal/`。

恢复演练使用原 MongoDB 镜像、全新目录和 `--internal` 隔离网络，导入逻辑归档后确认 comment=552、counter=21、config=1、cap_kv=0；原 Twikoo 镜像连接恢复库后 `GET_RECENT_COMMENTS` 返回 HTTP 200、5 条记录。未覆盖生产目录、未停止旧服务。

恢复顺序：验证 SHA256SUMS → 从 images.tar.gz 加载相同镜像 → 在新网络/新挂载启动 MongoDB → 将 mongo.archive.gz 通过标准输入传给容器内 `mongorestore --archive --gzip` → 核对集合、回复和配置 → 用相同 Twikoo 镜像连接新库验证读取。完整环境和凭据参考备份中的 `twikoo-inspect.private.json`，不得回显到公开日志。

脚本在仓库根运行，所有真实数据输出须放在仓库外：

```sh
# 基线备份：不停止服务
bash scripts/comments/backup-twikoo.sh baseline
# 从私有备份转换，输出目录必须是新目录
python3 scripts/comments/migrate.py convert <私有备份目录> <新转换目录> src/config/comment-paths.json
# 导入全新 SQLite 后逐条核对，成功才生成定位表
python3 scripts/comments/migrate.py verify <转换目录> <SQLite路径> <新定位表路径>
python3 scripts/comments/migrate.py avatars <转换目录> <新定位表路径> <新头像映射路径>
python3 scripts/comments/test_migrate.py
```

Artalk 使用 Python `sqlite3.Connection.backup()` 制作一致性快照，不复制运行中的 SQLite 单文件。私有备份、最终迁移源、配置、原镜像和 ID 映射至少保留 30 天，不自动删除。

候选快照批次：`20261025-171652-artalk-candidate`，服务器位于同一备份根目录。本机已验证归档与解包数据位于 `D:\Backups\Dusklight\comment-migration\20261025-171652-artalk-candidate-verified\`。归档哈希及 12 项文件哈希均通过；含 SQLite、运行/生产配置、管理员凭据、ID 映射和各层验收证据。后续候选快照使用 `scripts/comments/backup-artalk.py`。

适配前新增快照 `20261025-213536-artalk-candidate`：归档 SHA-256 为 `6ebc6f7b3f8c5fccff5e502774b0b8e71016441594e47ec43ceb59aa376bd0c0`，本机 `D:\Backups\Dusklight\comment-migration\20261025-213536-artalk-candidate-verified\` 内归档及解包后的 15 项文件校验一致，补充反代与空 OAuth 模板。该目录另存生产 `gh-pages` 提交 `75b8fbb` 的静态归档及其校验值；正式切换前需重新确认生产版本。此批次早于生成回源密钥和头像映射，不可替代最终备份。

## 正式切换与回退门槛

**以下步骤尚未执行；已获生产发布和正式切换授权，必须先通过全部验收门槛。**

1. 确认 EdgeOne HTTPS 与回源正常；API `/api/v2/` 不得缓存。当前候选反代以连接 IP 为准；正式放行前，通过上述回源密钥验证身份后再信任 `EO-Connecting-IP`，验证直接请求源站及伪造头部均不能绕过，避免把所有访客计为边缘节点。只改 Artalk 站点，不修改其他站点的全局 real-IP 设置。
2. 保存当前生产前端版本与静态产物。令 Twikoo 原入口进入维护，停止 `twikoo`；禁止旧缓存客户端继续写入。
3. 执行 `backup-twikoo.sh final`，脚本会拒绝 Twikoo 尚在运行的情况。逻辑备份和 JSON 核对完成后执行 `cold-backup-mongo.sh <最终备份目录>`：停止 MongoDB，冷备 `/data/db` 与 `/data/configdb` 的全部真实挂载，完成后只恢复 MongoDB。
4. 将最终备份复制到本机并通过哈希验证，执行隔离恢复演练。任一失败均不切换；保持维护或按旧服务回退。
5. 最终转换使用新目录，导入全新正式 SQLite，不能在候选库上追加全量数据；逐条验证后生成新锚点及 QQ 头像映射。更新两份前端映射并重新构建。停止候选 Artalk，再切换 Compose 挂载到最终数据目录；保留候选库原样。
6. 先验证最终库，再使用 `production.private.yml` 启用已验证 SMTP；发布前端产物并确认 CDN 生效后，移除候选反代中的 `limit_except` 开放写入。Twikoo 保持停止，不双写。
7. 上线即刻、24 小时及第 7 天检查提交/回复、审核、邮件、计数、路径与错误日志；比对其他容器的 ID 和启动时间，禁止顺带重建或升级其他服务。

若 Artalk 尚无新增写入，恢复旧前端/反代并启动 Twikoo。若已有新增或编辑，先停 Artalk 写入并制作一致性备份，导出差异、迁回并核对新评论/回复/状态后再恢复 Twikoo；**禁止只回退前端而遗漏新数据**。本次未执行任何回退或删除。

验证限制应如实记录：SMTP 接受不等于确认收到邮件；一次 API 200 不等于验证码或通知闭环；本次试迁移映射不等于正式最终映射。

## 验证与维护注意事项

- 迁移数据规则测试 4 项通过；固定版本网络错误修正测试 2 项通过。独立 QA API 验证了管理员登录、多层回复、Markdown/HTML、审核与置顶、待审隐藏、图片验证码及错误码拦截；QA 关闭真实通知。
- 受控 SMTP 邮件只发往原配置的博主邮箱，服务器已接受；尚未确认邮箱收件。候选生产数据未加入测试评论。
- 使用无头 Edge 验证首页 5 条最新评论、桌面 7 个页面及移动端 3 个页面的连续 ClientRouter 导航、快速换页、主题切换、旧 ID 定位及失败重试。滚动测量在 1440 和 390 宽度下均无横向溢出或长任务。
- Artalk 2.10.0 原生列表请求失败会在报告错误后重复抛出拒绝。`src/plugins/artalk-network-errors.mjs` 对固定 ESM 产物做精确的构建期修正，保留原生失败事件和重试逻辑；不修改 node_modules。升级时若匹配失效会阻止构建，必须重新检查上游。
- Artalk 配置须显式填写 `login_timeout: 259200`。部分配置文件不会自动补齐默认值；遗漏此字段会导致管理员令牌立即过期。正式配置只信任两个生产域名，预览域名仅在候选配置中。
- 评论 CSS 通过组件页面导入，由 ClientRouter 管理，不能仅靠缓存的动态 import 注入，否则换页后可能丢失样式；首页不加载评论编辑器资源。
- 原生 Astro 静态 redirect 会丢失 hash；旧页面使用轻量跳转页保留查询参数和锚点，不恢复已删除正文。`public/edgeone.json` 会复制到发布分支根，提供 8 条包含有/无尾斜杠的 HTTP 301 规则（按 [EdgeOne 官方格式](https://pages.edgeone.ai/document/edgeone-json)）；正式发布后必须验证 CDN 的参数与 hash 继承。Astro preview 的 `always` 模式会直接拒绝无尾斜杠路径，不应为此改动全站路由策略。
- 早期候选基线为 TypeScript 7，需要隔离 TypeScript 6 检查。当前实施分支已基于主线依赖修复提交 `0804897`（TypeScript 6.0.3），标准 `pnpm check` 通过：113 个文件、0 错误、0 警告、9 条提示；迁移和头像规则 6 项、固定版本网络修正 2 项测试通过。
- Windows Node 24 的字体钩子曾间歇性发生 FFI 退出崩溃（3221225477），以及隔离安装缺少 DLL。补齐本机同版本 DLL 后，使用与 CI 相同的临时 Node 22.23.4 完成标准 `pnpm build`，包含字体生成、Astro/Pagefind、静态审计、资源预算和 105 页后处理，退出码为 0。未修改字体工具链或项目依赖以规避该问题。
- 最终浏览器回归无未处理异常，旧路径跳转保留参数与锚点，失败请求重试恢复；8 条网关规则只完成配置校验，尚未发布到生产 CDN。首页样式总量 108312 字节，低于 130 KiB 预算。
- 新适配回归覆盖 419 条头像映射、页面 28 张 QQ 头像实际加载、5 张图片内容哈希互不相同、主评论/侧栏一致性，以及 QQ 请求失败后仅回退一次。1440/390 宽度明暗主题无横向溢出，预览、表情、回复及取消通过。另跑完整路由/滚动/断网回归，未处理异常为 0、滚动长任务为 0。原始截图与报告仅保存在私有验收副本，不发布到博客仓库。
