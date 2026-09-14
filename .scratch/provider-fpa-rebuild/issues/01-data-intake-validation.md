# 01: Data Intake & Validation

Status: ready-for-agent

**What to build:** 用户打开网站后可主动载入合成演示数据，检查输入状态，并选择 Clinic-Month 进入后续工作流。用最小可用的数据入口贯通界面、读取和校验。

**Blocked by:** None (can start immediately)

## Acceptance criteria

- [ ] 默认无数据状态解释所需输入；一键载入演示数据，页面持续标明 Synthetic Benchmark，不显示冒充真实数据的结果。
- [ ] 支持现有 benchmark 的五类逻辑输入：Clinic、Financial Value、Operational Value、Operating Event、Review Rule；可通过符合已知契约的 CSV 导入同类合成数据，不实现客户文件适配或通用字段映射器。
- [ ] 检查 Clinic 引用、Calendar Month、必要字段、重复记录、单位、币种与 Source Reference；错误定位到输入记录。结构性错误阻止导入；可表达的数值缺失保留为不可用并进入后续 Data Quality Issue 展示。
- [ ] 用户能选择有效 Clinic-Month 并看到数据来源、有效性及可用比较基准；不猜测真实关账状态或预测批准信息。
- [ ] 聚合数据边界明确，不接受超出契约的个人级标识；无数据库、账户系统或外部数据连接。
- [ ] 通过公开输入入口验证成功载入、无数据、重复／无效输入和故意缺失数据场景；不修改保留的 benchmark 标准答案。

## Parent and agreed scope

Parent: Provider FP&A 网站重建规格（同一 feature 的 spec）。

2026-09-14 用户已确认将原九项拆分收敛为五个 outcome-oriented milestones，以求职 portfolio 和今晚 demo 为目标。优先贯通 clinic-month → variance → evidence → driver → AI commentary → human review。本文记录最新范围；原规格与需求文档保持不变。

今晚不做真实数据集成、复杂权限、数据库或生产级架构。使用明确标记的合成数据；真实数据适配及业务验收延期。各类 driver 场景是同一 investigation workflow 的 benchmark cases，不建独立 UI features。不要恢复旧实现或从旧测试报告推断新实现已经通过验收。

每项交付应包含可演示的用户行为和对应验证；不拆成前端、后端、数据库等水平任务。保留领域术语和证据边界；在编辑前及工作完成后保存 Git 提交。
