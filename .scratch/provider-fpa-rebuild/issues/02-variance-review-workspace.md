# 02: Variance Review Workspace

Status: ready-for-agent

**What to build:** 用户选择 Clinic-Month 后，在同一工作区核对差异并从 Review Queue 打开一个待调查事项，为完整演示提供真实可计算的起点。

**Blocked by:** 01 — Data Intake & Validation

## Acceptance criteria

- [ ] 展示实际值、Latest Approved Forecast／明确的经营比较值、差额、可计算的百分比，以及进入 Review Queue 的原因。
- [ ] 区分 Financial Variance、Operational Metric Variance、Forecast Assumption Variance；差额符号与有利／不利方向分开显示。零或缺失分母显示不可计算及原因。
- [ ] Materiality Rule 使用金额或百分比任一严格超过阈值；支持 Critical Metric Rule 和 Analyst Override。规则筛选不交给 LLM。
- [ ] Clinic-Month、指标、来源与比较版本在选中事项中保持一致；缺少有效比较基准时阻止相应计算。
- [ ] 使用一个连贯工作区呈现选择、队列与差异详情；后续证据、解释和审核在该工作流中展开，不为不同 driver 建新产品页面。
- [ ] 验证计算、阈值恰好相等、手动加入、缺失比较值，以及切换 Clinic-Month 不混入其他事项。

## Parent and agreed scope

Parent: Provider FP&A 网站重建规格（同一 feature 的 spec）。

2026-09-14 用户已确认将原九项拆分收敛为五个 outcome-oriented milestones，以求职 portfolio 和今晚 demo 为目标。优先贯通 clinic-month → variance → evidence → driver → AI commentary → human review。本文记录最新范围；原规格与需求文档保持不变。

今晚不做真实数据集成、复杂权限、数据库或生产级架构。使用明确标记的合成数据；真实数据适配及业务验收延期。各类 driver 场景是同一 investigation workflow 的 benchmark cases，不建独立 UI features。不要恢复旧实现或从旧测试报告推断新实现已经通过验收。

每项交付应包含可演示的用户行为和对应验证；不拆成前端、后端、数据库等水平任务。保留领域术语和证据边界；在编辑前及工作完成后保存 Git 提交。
