# 03: Evidence-Backed Investigation

Status: ready-for-agent

**What to build:** 用户从差异详情进入同一调查流程，沿证据追溯到有支持的经营驱动及其边界。先贯通一个有来源的 provider availability 案例，再扩展同一契约覆盖其他 benchmark cases。

**Blocked by:** 02 — Variance Review Workspace

## Acceptance criteria

- [ ] 在同一工作区分开展示 Observed Fact、Supporting Evidence、Operating Driver 与 Conclusion，每条关键事实／证据可追溯到具体 Source Reference。
- [ ] 主展示案例贯通 clinic-month → variance → evidence → driver，说明直接 Primary Driver 和上游 Contributing Driver，不能用上游事件跳过直接经营机制。
- [ ] 同一分析入口支持 provider availability、weather、labor、payer mix、accounting timing、seasonality、multiple drivers，以及无解释和数据质量场景；不为它们分别实现 UI 功能或独立分析入口。
- [ ] 采用七类 Driver Family 及 Other、Unresolved、Data Quality Issue；保留 Candidate、Supported、Rejected、Unresolved 状态，不自动赋予 Analyst-Confirmed Cause。
- [ ] 显示 Forecast Horizon 及 Temporary／Structural／Unresolved 判断依据；按 ADR 明示后备期间，Recurring Pattern 与结构性分开。无法判断时不补造结论。
- [ ] 无定量证据时 Contribution Estimate 未知；多驱动无法排序时明确未解决。缺失证据不视为反证，并提供下一步调查问题。
- [ ] 通过统一调查公共边界验证所用 benchmark cases 及禁止结论。Expected Answer Contract 仅供评估器读取；分析不能读取 gold 或依赖案例编号输出答案。
- [ ] 优先完成主展示案例及一个未解决案例后接入下一里程碑，再补齐剩余案例；本里程碑关闭前仍需覆盖全部调查场景。

## Parent and agreed scope

Parent: Provider FP&A 网站重建规格（同一 feature 的 spec）。

2026-09-14 用户已确认将原九项拆分收敛为五个 outcome-oriented milestones，以求职 portfolio 和今晚 demo 为目标。优先贯通 clinic-month → variance → evidence → driver → AI commentary → human review。本文记录最新范围；原规格与需求文档保持不变。

今晚不做真实数据集成、复杂权限、数据库或生产级架构。使用明确标记的合成数据；真实数据适配及业务验收延期。各类 driver 场景是同一 investigation workflow 的 benchmark cases，不建独立 UI features。不要恢复旧实现或从旧测试报告推断新实现已经通过验收。

每项交付应包含可演示的用户行为和对应验证；不拆成前端、后端、数据库等水平任务。保留领域术语和证据边界；在编辑前及工作完成后保存 Git 提交。
