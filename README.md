# valuation-comps

> 给一个标的，自动跑完可比公司分析（trading comps）的八步流程，输出对齐口径的 Comps 表与隐含估值区间。
> 投资分析的第一性工具——**相对估值锚**。不预测点位，只回答"市场现在愿为这类生意付多少倍"。

设计哲学：代码只是表达媒介，**能复用、能复现、能校验**才值得做（致敬 Zara Zhang 的 `frontend-slides`）。

## 为什么可靠
- **口径强制对齐**：脚本统一处理 EV（含净负债）与 P/E（不含）的换算，避免混用失真。
- **算术交给脚本**：`scripts/comps_calc.py` 计算中位数/分位与隐含区间，agent 不心算。
- **N/A 不编造**：缺数自动跳过该样本并标注，绝不填占位假数。
- **冲突强制复盘**：与 DCF 偏离 >20% 时禁止直接下结论。

## 快速开始

```bash
# 1) 准备输入（peer 倍数 + 标的预测指标），JSON 见 examples/input.json
python3 scripts/comps_calc.py --input examples/input.json

# 2) 自测（验证算术可靠）
python3 scripts/comps_calc_test.py
```

输入 JSON 结构：
```json
{
  "net_debt": 1200,            // 标的净负债（百万元），EV→权益换算用
  "shares": 800,               // 标的总股本（百万股），算每股用
  "target": {                  // 标的预测指标（与倍数同口径）
    "revenue": 5000, "ebitda": 900, "eps": 2.5
  },
  "peers": [
    {"name": "Peer A", "EV/Revenue": 4.2, "EV/EBITDA": 14.1, "P/E": 22.0},
    {"name": "Peer B", "EV/Revenue": 3.6, "EV/EBITDA": 12.8, "P/E": 19.5}
  ]
}
```

## 八步流程（详见 SKILL.md）
1. 定标的与视角 → 2. 三维选 peer → 3. 取倍数 → 4. 对齐口径 → 5. 算中心趋势 → 6. 敏感性区间 → 7. 隐含校验 → 8. 出结论 + 重估触发变量。

## 数据来源（严禁编造）
- 首选 `westock-data`（A/港/美结构化数据，含 NTM/FY+1 一致预期）；
- 备选 `akshare-stock` / `neodata-financial-search`；
- 兜底 `WebSearch` / 公司 IR / 年报。缺失标 `N/A`。

## 与同系列 skill 的关系
- `dcf-quick`：绝对估值锚（它值多少钱）——本 skill 的相对锚与之交叉验证。
- `macro-dashboard`：自上而下的攻守开关——决定"现在该不该满仓买"。
- 三者构成：宏观开关 → 选股（comps） → 定价（dcf）的闭环。

## 许可
MIT。分析结论仅供参考，投资决策由人负责。
