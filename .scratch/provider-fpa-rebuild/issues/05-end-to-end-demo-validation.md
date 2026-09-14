# 05: End-to-End Demo & Validation

Status: ready-for-agent

**What to build:** 交付可重复启动和演示的 portfolio 作品：一个完整主案例、一个诚实保留未解决结论的对照案例，以及可复核的验证结果和简短演示说明。

**Blocked by:** 03 — Evidence-Backed Investigation 全部案例完成；04 — AI Commentary + Human Review

## Acceptance criteria

- [ ] 从无数据首页开始，经主动载入合成数据、选择 Clinic-Month、查看 variance、追溯 evidence、解释 driver、生成 commentary 到 human review，完成浏览器端到端验证。
- [ ] 同一工作流验证十个 Synthetic Benchmark cases 的七个维度及 Forbidden Conclusion；标准答案不泄漏给被测分析流程，不将旧报告当作新结果。
- [ ] 验证未解决和 Data Quality Issue 案例可以正确结束调查，但不能被误报为已确认解释。人工操作前不得存在自动确认的原因。
- [ ] 保证主演示链路的空状态、加载、错误提示、证据阅读和审核操作清晰；优化演示可读性，不增设独立 driver 页面。
- [ ] 新增简短 demo 操作说明，包含启动、主案例、未解决对照、重置和模型不可用的演示方式；不改写原需求文档。
- [ ] 提供准确的 portfolio 描述及验证记录：合成数据、实际完成能力、实时 AI 或 fallback 状态、测试结果与限制。不声称真实业务数据验证、生产就绪或经过真实用户成效评估。
- [ ] 审核记录可重置，重复演示结果可解释；不需要数据库、复杂权限、真实数据集成或生产部署即可运行。
- [ ] 若缺少模型凭证，只能交付明确标识的 fallback 演示并记录实时 AI 验收未完成；不能以离线 mock 测试冒充真实 AI 成功。

## Parent and agreed scope

Parent: Provider FP&A 网站重建规格（同一 feature 的 spec）。

2026-09-14 用户已确认将原九项拆分收敛为五个 outcome-oriented milestones，以求职 portfolio 和今晚 demo 为目标。优先贯通 clinic-month → variance → evidence → driver → AI commentary → human review。本文记录最新范围；原规格与需求文档保持不变。

今晚不做真实数据集成、复杂权限、数据库或生产级架构。使用明确标记的合成数据；真实数据适配及业务验收延期。各类 driver 场景是同一 investigation workflow 的 benchmark cases，不建独立 UI features。不要恢复旧实现或从旧测试报告推断新实现已经通过验收。

每项交付应包含可演示的用户行为和对应验证；不拆成前端、后端、数据库等水平任务。保留领域术语和证据边界；在编辑前及工作完成后保存 Git 提交。
