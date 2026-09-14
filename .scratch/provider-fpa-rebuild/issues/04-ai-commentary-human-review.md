# 04: AI Commentary + Human Review

Status: ready-for-agent

**What to build:** 用户对选中调查生成有依据的管理层 commentary，然后显式审核原因与假设建议，完成今晚最有价值的完整 vertical slice。

**Blocked by:** 03 — Evidence-Backed Investigation 的主展示及未解决案例公共契约已验证；不等待其余 driver cases 全部完成

## Acceptance criteria

- [ ] commentary 使用已验证的结构化调查结果，包含关键差异、支持的驱动、证据缺口、经营追问、预测考虑及人工审核提示；所有数字和来源可核对。
- [ ] 使用单一轻量模型连接，前提是已有可用且获授权的凭证；只发送合成演示数据，不为本 demo 构建通用模型平台。密钥不写进前端、仓库或输出。
- [ ] 无模型配置、请求失败或输出校验失败时显示明确状态，并可使用确定性摘要继续演示。页面和演示材料必须区分实时 AI 生成与模板摘要；fallback 不得算作实时 AI 调用已验收。
- [ ] AI 不重算差异、不赋予 Analyst-Confirmed Cause、不隐去重要未解决状态、不生成无依据的贡献估计，也不改写实际预测。对无效输出拒绝展示为有效 commentary。
- [ ] 分别提供 Supported Driver 的人工确认／拒绝，以及 Assumption-Change Proposal 的接受／拒绝／进一步调查；保存理由、时间及关联的调查／数据版本。
- [ ] 使用浏览器本地存储保留 demo 审核记录，刷新后可见，并提供明确的重置演示操作；不建立数据库、复杂权限或生产审计系统。告知其只保存在当前浏览器，不声称具备生产身份认证。
- [ ] 显示 Successful Investigation 与 Successfully Explained Variance 的不同含义；没有显式人工确认或仍存在影响结论的重大未解决事项时，不显示成功解释。
- [ ] 验证完整主案例、未解决案例、模型不可用／不合规输出、显式审核、刷新留存和跨调查隔离。离线测试使用可控响应；实时 AI 是否验证成功单独记录。

## Parent and agreed scope

Parent: Provider FP&A 网站重建规格（同一 feature 的 spec）。

2026-09-14 用户已确认将原九项拆分收敛为五个 outcome-oriented milestones，以求职 portfolio 和今晚 demo 为目标。优先贯通 clinic-month → variance → evidence → driver → AI commentary → human review。本文记录最新范围；原规格与需求文档保持不变。

今晚不做真实数据集成、复杂权限、数据库或生产级架构。使用明确标记的合成数据；真实数据适配及业务验收延期。各类 driver 场景是同一 investigation workflow 的 benchmark cases，不建独立 UI features。不要恢复旧实现或从旧测试报告推断新实现已经通过验收。

每项交付应包含可演示的用户行为和对应验证；不拆成前端、后端、数据库等水平任务。保留领域术语和证据边界；在编辑前及工作完成后保存 Git 提交。

## Dependency handoff

03 的主案例与未解决案例均有可验证的公开调查结果后即可开始 04；03 余下 benchmark 覆盖不阻塞主链路接通。这是同一里程碑内的交付检查点，不新增第六张任务。最终验收必须等待 03 全部完成。
