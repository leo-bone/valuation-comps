#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
valuation-comps 计算内核。

职责：输入 peer 倍数 + 标的预测指标，输出
  1) 每个倍数的 中位数 / 均值 / 25 / 75 分位；
  2) 用分位倍数 × 标的指标得到的隐含估值区间（每股）；
  3) 异常值标记与口径校验。

设计原则：
  - 不联网、不编造；N/A 或负基数自动跳过该样本并标注。
  - agent 只负责取数和对齐口径，算术交给本脚本，避免心算误差。
  - EV 系倍数（含净负债）与 P/E（不含）的换算自动处理。

用法：
  python3 comps_calc.py --input input.json
  python3 comps_calc.py --selftest
"""
import json
import sys
import argparse


# 倍数规格：base=EV 表示隐含企业价值（需减净负债得权益）；base=Equity 表示直接给每股价
MULTIPLE_SPEC = {
    "EV/Revenue":    {"metric": "revenue",     "base": "EV"},
    "EV/EBITDA":     {"metric": "ebitda",      "base": "EV"},
    "EV/GrossProfit":{"metric": "gross_profit","base": "EV"},
    "P/E":           {"metric": "eps",         "base": "Equity"},
}


def percentile(values, p):
    """线性插值分位数（与 numpy 'linear' 一致）。"""
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def clean(peers):
    """把 peer 中有效（非 None、非负基数对应倍数）的样本抽出。"""
    rows = []
    skipped = []
    for p in peers:
        row = {"name": p.get("name", "?")}
        valid = True
        for mult in MULTIPLE_SPEC:
            v = p.get(mult)
            if v is None or (isinstance(v, str) and v.strip().upper() == "N/A"):
                row[mult] = None
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                row[mult] = None
                continue
            if fv < 0:  # 负基数无意义
                row[mult] = None
                skipped.append((p.get("name", "?"), mult, "负基数"))
                continue
            row[mult] = fv
        rows.append(row)
    return rows, skipped


def analyze(data):
    net_debt = float(data.get("net_debt", 0) or 0)
    shares = float(data.get("shares", 0) or 0)
    target = data.get("target", {})
    rows, skipped = clean(data.get("peers", []))

    out = {"sample_count": len(rows), "skipped": skipped, "multiples": {}}

    for mult, spec in MULTIPLE_SPEC.items():
        vals = [r[mult] for r in rows if r.get(mult) is not None]
        if not vals:
            out["multiples"][mult] = {"available": 0, "note": "无有效样本"}
            continue
        med = percentile(vals, 50)
        p25 = percentile(vals, 25)
        p75 = percentile(vals, 75)
        mean = sum(vals) / len(vals)

        entry = {
            "available": len(vals),
            "median": round(med, 2),
            "mean": round(mean, 2),
            "p25": round(p25, 2),
            "p75": round(p75, 2),
        }

        # 隐含估值（每股）
        metric_val = target.get(spec["metric"])
        if metric_val is not None and shares > 0:
            try:
                mv = float(metric_val)
                if spec["base"] == "EV":
                    # 隐含 EV = 倍数 × 指标；权益 = EV − 净负债；每股 = 权益 / 股本
                    imp_p25 = (p25 * mv - net_debt) / shares
                    imp_med = (med * mv - net_debt) / shares
                    imp_p75 = (p75 * mv - net_debt) / shares
                else:  # Equity（P/E）：每股价 = 倍数 × EPS
                    imp_p25 = p25 * mv
                    imp_med = med * mv
                    imp_p75 = p75 * mv
                entry["implied_per_share"] = {
                    "p25": round(imp_p25, 2),
                    "median": round(imp_med, 2),
                    "p75": round(imp_p75, 2),
                }
            except (TypeError, ValueError):
                pass

        # 异常值标记：偏离中位数 > 2× 提示复核
        outliers = []
        for r in rows:
            if r.get(mult) is not None and med and (r[mult] > med * 2 or r[mult] < med * 0.5):
                outliers.append(r["name"])
        if outliers:
            entry["outliers"] = outliers

        out["multiples"][mult] = entry

    return out


def render_md(out, data):
    lines = []
    lines.append(f"**样本数**：{out['sample_count']} 家 peer")
    if out["skipped"]:
        lines.append(f"**跳过样本**（负基数/ N/A）：{out['skipped']}")
    lines.append("")
    lines.append("| 倍数 | 可用样本 | 中位数 | 均值 | 25 分位 | 75 分位 | 隐含每股(25/中/75) |")
    lines.append("|---|---|---|---|---|---|---|")
    for mult, e in out["multiples"].items():
        if e.get("available", 0) == 0:
            lines.append(f"| {mult} | 0 | — | — | — | — | 无有效样本 |")
            continue
        imp = e.get("implied_per_share")
        imp_s = f"{imp['p25']} / {imp['median']} / {imp['p75']}" if imp else "—"
        outl = f" ⚠️异常:{e['outliers']}" if e.get("outliers") else ""
        lines.append(f"| {mult} | {e['available']} | {e['median']}x | {e['mean']}x | {e['p25']}x | {e['p75']}x | {imp_s}{outl} |")
    lines.append("")
    lines.append("> 计算内核：`scripts/comps_calc.py`。所有倍数需注明口径（LTM/NTM/FY+1）与币种；")
    lines.append("> 与 `dcf-quick` 偏离 >20% 时必须复盘口径或 peer 选择。")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="输入 JSON 路径")
    ap.add_argument("--selftest", action="store_true", help="跑内置自检")
    args = ap.parse_args()

    if args.selftest:
        import comps_calc_test
        sys.exit(0 if comps_calc_test.run() else 1)

    if not args.input:
        print("⛔ 需提供 --input <json> 或 --selftest")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = analyze(data)
    print(render_md(out, data))


if __name__ == "__main__":
    main()
