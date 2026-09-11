# 从头重建 Provider FP&A 网站

Status: ready-for-agent

确认日期：2026-09-10

## Problem Statement

用户已弃用旧网站并删除全部实现，希望保留原有文档，从头构建 Provider FP&A MVP。当前仓库保留了需求、领域术语、ADR 和 Synthetic Benchmark，但没有可运行的应用。历史实现说明和测试报告仅作为参考，不能证明新应用已经具备功能或通过验证。

Provider FP&A Analyst 需要调查多诊所专科 Provider Organization 的 Closed Month 实际值相对 Latest Approved Forecast 的 Financial Variance，查看可追溯的经营证据，并审核 Assumption-Change Proposal。

用户将在之后提供数据。现阶段不能假设已经获得真实业务数据，也不能把 Synthetic Benchmark 描述成用户数据。

## Solution

构建支持以下完整流程的网站：导入 Clinic-Month Dataset → 查看 Review Queue → 检查 Variance Explanation 与 Supporting Evidence → 人工审核 Assumption-Change Proposal。

无数据时提供清晰的导入入口、五类逻辑输入的说明及缺失项提示。真实数据提供前，用明确标注为合成数据的 Synthetic Benchmark 验证流程；只有用户主动选择演示数据时才展示演示结果，不默认生成真实业务结论。

真实数据到达后，根据其实际格式核对字段映射、单位、月份、来源、关账状态及批准预测版本。上述信息未满足契约时明确阻止受影响的分析，不补造值、不暗中选择比较基准。具体客户文件适配及真实数据验收依赖后续数据交付。

现有文档保持原样。新实现遵循现有领域术语及四项 ADR，不恢复旧网站的页面或技术选型作为默认要求。

## User Stories

1. As an 项目所有者, I want 从空白实现重建网站并保留原文档, so that 我可以重新设计产品而不丢失需求。
2. As an Provider FP&A Analyst, I want 无数据时看到需要准备的输入, so that 我可以在之后提供数据。
3. As an Provider FP&A Analyst, I want 主动选择明确标注的合成演示数据, so that 我能先检查工作流程。
4. As an Provider FP&A Analyst, I want 导入 Clinic、Financial Value、Operational Value、Operating Event 和 Review Rule 五类逻辑输入, so that 分析拥有统一的数据基础。
5. As an Provider FP&A Analyst, I want 查看字段、单位、月份和来源校验结果, so that 我能修正影响分析的问题。
6. As an Provider FP&A Analyst, I want 收到可定位到输入记录的重复、缺失或无效数据提示, so that 我能追溯错误。
7. As an Provider FP&A Analyst, I want 明确选择 Clinic 和 Closed Month, so that 不同诊所和月份的事实不会混淆。
8. As an Provider FP&A Analyst, I want 知道所用的 Latest Approved Forecast 及其批准状态, so that 比较基准可靠。
9. As an Provider FP&A Analyst, I want 分别查看 Financial Variance、Operational Metric Variance 和 Forecast Assumption Variance, so that 不同概念不会混为一谈。
10. As an Provider FP&A Analyst, I want 查看实际值、比较值、差额和可计算的百分比, so that 我能核对计算。
11. As an Provider FP&A Analyst, I want 分母为零或缺失时看到不可计算原因, so that 我不会误读伪造的百分比。
12. As an Provider FP&A Analyst, I want 使用可配置的 Materiality Rule 和 Critical Metric Rule, so that Review Queue 符合业务要求。
13. As an Provider FP&A Analyst, I want 通过 Analyst Override 加入需要调查的 Variance, so that 未超过阈值的重要事项仍能处理。
14. As an Provider FP&A Analyst, I want 看到每项进入 Review Queue 的原因, so that 我能核查筛选规则。
15. As an Provider FP&A Analyst, I want 分开查看 Observed Fact、Supporting Evidence、Operating Driver 和 Conclusion, so that 我能辨别事实与解释。
16. As an Provider FP&A Analyst, I want 从证据查看 Source Reference, so that 我能追溯对应记录。
17. As an Provider FP&A Analyst, I want 区分直接的 Primary Driver 和上游的 Contributing Driver, so that 解释符合经营机制。
18. As an Provider FP&A Analyst, I want 证据不足时保留 Candidate 或 Unresolved 状态及待调查问题, so that 系统不会编造原因。
19. As an Provider FP&A Analyst, I want 看到矛盾证据和 Data Quality Issue, so that 我能判断结论的限制。
20. As an Provider FP&A Analyst, I want 缺少定量依据时 Contribution Estimate 保持未知, so that 分摊数字不会误导决策。
21. As an Provider FP&A Analyst, I want 依据明确的 Forecast Horizon 查看 Timing Classification, so that 我能判断预测假设是否需要复核。
22. As an Provider FP&A Analyst, I want 将 Recurring Pattern 与 Temporary、Structural 分开理解, so that 季节性不会自动被视为结构性变化。
23. As an Provider FP&A Analyst, I want 查看保留、情景测试或重新考虑假设的 Assumption-Change Proposal, so that 我能决定下一步行动。
24. As an Provider FP&A Analyst, I want 显式确认或拒绝 Supported Driver, so that Analyst-Confirmed Cause 只来自人工决定。
25. As an Provider FP&A Analyst, I want 接受、拒绝或要求进一步调查 Assumption-Change Proposal, so that 假设建议有明确审核结果。
26. As an Provider FP&A Analyst, I want 刷新后仍能查看审核决定、时间和理由, so that 审核过程可追溯。
27. As an Provider FP&A Analyst, I want 清楚知道审核建议不会写入实际预测, so that 我能保持对财务系统的控制。
28. As an 项目所有者, I want 使用十个固定案例验证所需结论与 Forbidden Conclusion, so that 新实现不会只是在界面上看似合理。
29. As an 项目所有者, I want 区分 Successful Investigation 与 Successfully Explained Variance, so that 正确保留未解决问题也能得到合理评价。
30. As an 项目所有者, I want 在收到真实数据后单独完成适配及验收, so that 演示通过不会被误认为真实业务验证通过。

## Implementation Decisions

- 已确认范围为上述端到端流程，且用户之后提供数据。本规格授权的是需求整理；编码、部署和外部服务连接不是本次规格编写工作的组成部分。
- 逻辑职责包括数据导入与校验、确定性计算与队列筛选、证据约束的调查、人工审核记录，以及网站展示。具体语言、框架、视觉设计和部署方式尚未指定，由后续实现结合仓库规则决定。
- 采用统一的调查工作流公共边界：接收有效的五类逻辑输入及 Clinic-Month 选择，返回结构化调查结果；人工审核通过显式用户操作更新对应审核状态。业务规则不依赖页面布局，避免每次界面改动都重写分析逻辑。该长期方案的成本是需要明确的数据契约和持久化审核记录。
- 初始文件导入可支持符合逻辑契约的 CSV，与现有 Synthetic Benchmark 对齐。用户未来文件的实际格式、列名、币种及预测治理信息均未确认；不得预先声称兼容任意 Excel 或客户系统导出。
- 所有分析记录保留 Clinic、统一的 Calendar Month、指标身份、单位、币种及 Source Reference。来源引用应足以定位到输入文件或数据集中的具体记录。真实数据不适合既定契约时先报告差异，不改变原文档来迁就输入。
- MVP 只接收聚合的 Clinic-Month 数据，不包含个人级患者、员工、provider、理赔或 encounter 标识。Market 仅用于聚合，不能取代 Clinic-Month 解释单位。
- Financial Variance 使用实际减批准预测；经营指标使用实际减明确的预期值。百分比保持精度后再判断阈值；零或缺失分母返回不可计算及原因。差额符号和有利／不利方向分开表达。
- Materiality Rule 按严格超过阈值判断；金额或百分比任一超过即符合筛选条件。Critical Metric Rule 和 Analyst Override 可独立加入队列。LLM 不决定重要性。历史生成器说明中的阈值差异不能沿用为新规则。
- 采用领域文档中的七个 Driver Family，以及 Other、Unresolved、Data Quality Issue。主驱动需有直接经营机制与证据支撑；无法区分多个候选直接机制时明确未解决，不强行排序。
- Observed Fact、Supporting Evidence、Candidate/Supported/Rejected/Unresolved Driver 与 Conclusion 分开保存和展示。AI 不能产生 Analyst-Confirmed Cause，缺失证据不等于反证。
- Contribution Estimate 仅在定量支持充分时出现；金额及比例必须与输入可核对，不用语言模型猜测。
- Timing Classification 使用剩余批准预测期间；没有 Latest Approved Forecast 时，按 ADR 明示未来三个月的后备 Forecast Horizon。后备期间不授权补造财务比较值。Recurring Pattern 不自动意味着 Structural；证据不足时为 Unresolved。
- Assumption-Change Proposal 是建议。审核建议与确认原因是不同操作；接受建议不写入 ERP、总账、预算或预测。审核保存所关联的调查与数据版本、决定、时间、理由及可用的审核者标识；本地标识不等同于生产身份认证。
- 网站文案以结构化结果为依据。若后续采用 AI narrative，它不能重新计算数字、改变驱动证据状态、隐去关键缺口或暗示自动确认；没有模型连接时仍能呈现完整且诚实的结构化结果。真实数据的外部传输未获本次授权。
- Synthetic Benchmark 的输入与 Expected Answer Contract 隔离，只有评估器读取标准答案。分析流程不得按案例编号、诊所编号或预置答案生成结果。

## Testing Decisions

- 用户已确认最高层验收边界：导入数据 → Review Queue → 解释与证据 → 人工审核建议；其后补充数据将在之后提供，其余同意。
- 主要自动化分析测试集中在统一调查工作流公共边界，断言输入所应产生的可观察结果，不锁定内部函数、模块数量或页面实现细节。少量浏览器测试覆盖完整流程、无数据状态、无效输入、证据追溯和审核持久化。
- 通行方法依据 Playwright 的用户可见行为测试建议，以及 Practical Test Pyramid 对业务测试和少量端到端测试的分工。此处不指定必须使用某一浏览器测试框架。
- 沿用现存十个 Benchmark Case 与七个评估维度：Observed Variance、Driver Family、主次驱动角色、Timing Classification、epistemic state、人工审核要求、Forbidden Conclusion。旧测试代码已删除，历史报告只能作先例，必须重新运行新实现。
- 十种场景覆盖 PTO、人员离职、天气关闭、无解释的就诊量下降、加班费用、支付实现变化、会计计提时点、无效经营输入、季节性、多驱动。
- 专门验证严格阈值边界、零／缺失分母、重复记录、跨 Clinic-Month 证据污染、无批准比较基准，以及不支持的指标或机制仍明确未解决。
- 证据不足的案例应允许 Successful Investigation 为真而 Successfully Explained Variance 为假；后者必须经过人工确认并且无未披露的重大未解决事项。未经人工操作所有自动结果均不得成为 Analyst-Confirmed Cause。
- 审核测试通过公开操作验证确认、拒绝、要求调查与刷新后保存的记录，并验证不会改变原始数据、实际预测或其他 Clinic-Month 的结论。
- 若接入 AI narrative，验证输出保留正确数字、来源和未解决状态，拒绝无证据的结论；不以关键词检查单独证明语义正确。
- 当前验收只覆盖合成数据与输入契约。真实数据到达后，另行核对字段映射、来源、关账与预测版本，并由用户核对代表性结果。未完成这一步不能宣称已通过真实业务验收。

## Out of Scope

- 修改、删除或重写原有需求文档及 ADR。
- 在本次 to-spec 任务中编写应用代码、恢复旧实现或部署网站。
- 在用户交付前假定真实数据格式，生成冒充真实数据的结果，或宣称真实数据验收完成。
- 医院、服务线、患者或个人 encounter 层分析，实时分析，多预测版本对比，预算或去年同期比较。
- Market Intelligence Module、外部新闻监控、自动抓取业务数据。
- 自动确认原因、自动更改预测／预算／总账，以及未经授权向外部模型传输用户数据。
- 生产多租户、企业身份认证、客户系统连接器和完整生产上线治理；如需这些能力须单独明确范围。

## Further Notes

- 本规格根据用户“文档不变、删除编程、从头开始”的指示、对主要验收流程的确认及“之后会给数据”的补充整理。保留文档中的产品范围和 ADR 仍有效，旧代码的模块结构、CLI 命令和测试结果不构成新实现约束或完成证据。
- Status 为 ready-for-agent 表示可以按本规格开始合成数据支持下的重建工作，不表示真实数据已经准备好或产品已经完成。
- 后续真实数据适配需在数据交付后才能具体化；当前不为此虚构输入细节，也不阻止先完成通用流程。
- 参考：[Playwright Best Practices](https://playwright.dev/docs/best-practices)、[The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)。
