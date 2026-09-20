#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comps_calc 单测：保证算术与口径换算可靠。"""
import comps_calc as C


def run():
    ok = True

    # 1) 分位数（线性插值）正确性
    vals = [1, 2, 3, 4]
    assert abs(C.percentile(vals, 50) - 2.5) < 1e-9, "median 4 个元素应为 2.5"
    assert abs(C.percentile(vals, 25) - 1.75) < 1e-9, "p25 应为 1.75"
    assert abs(C.percentile(vals, 75) - 3.25) < 1e-9, "p75 应为 3.25"
    assert C.percentile([7], 50) == 7, "单元素返回自身"
    assert C.percentile([], 50) is None, "空返回 None"

    # 2) EV 系隐含每股： (倍数×指标 − 净负债)/股本
    data = {
        "net_debt": 1000, "shares": 100,
        "target": {"revenue": 1000, "ebitda": 200, "eps": 5},
        "peers": [
            {"name": "A", "EV/Revenue": 4.0, "EV/EBITDA": 15.0, "P/E": 20.0},
            {"name": "B", "EV/Revenue": 5.0, "EV/EBITDA": 17.0, "P/E": 22.0},
            {"name": "C", "EV/Revenue": 6.0, "EV/EBITDA": 19.0, "P/E": 24.0},
        ],
    }
    out = C.analyze(data)
    evr = out["multiples"]["EV/Revenue"]
    # 中位数 = 5.0；隐含每股 median = (5.0*1000 - 1000)/100 = 40.0
    assert abs(evr["median"] - 5.0) < 1e-9, "EV/Rev 中位数应为 5.0"
    assert abs(evr["implied_per_share"]["median"] - 40.0) < 1e-9, "EV/Rev 隐含每股应为 40.0"

    # 3) P/E 隐含每股 = 倍数 × EPS（不含净负债）
    pe = out["multiples"]["P/E"]
    # 中位数 = 22.0；隐含每股 median = 22.0*5 = 110.0
    assert abs(pe["implied_per_share"]["median"] - 110.0) < 1e-9, "P/E 隐含每股应为 110.0"

    # 4) N/A 与负基数跳过且不崩溃
    data2 = {
        "net_debt": 0, "shares": 100,
        "target": {"revenue": 1000, "ebitda": 200, "eps": 5},
        "peers": [
            {"name": "A", "EV/Revenue": 4.0, "EV/EBITDA": 15.0, "P/E": 20.0},
            {"name": "B", "EV/Revenue": "N/A", "EV/EBITDA": -5.0, "P/E": 22.0},  # 负 EBITDA 跳过
        ],
    }
    out2 = C.analyze(data2)
    assert out2["multiples"]["EV/Revenue"]["available"] == 1, "EV/Rev 应只剩 1 个有效样本"
    assert out2["multiples"]["EV/EBITDA"]["available"] == 1, "负 EBITDA 跳过 B，A 的 15.0 仍有效"
    assert ("B", "EV/EBITDA", "负基数") in out2["skipped"], "应记录负基数跳过"

    # 5) 异常值标记（偏离中位数 >2×）
    data3 = {
        "net_debt": 0, "shares": 100,
        "target": {"revenue": 1000, "ebitda": 200, "eps": 5},
        "peers": [
            {"name": "A", "EV/Revenue": 4.0, "EV/EBITDA": 15.0, "P/E": 20.0},
            {"name": "B", "EV/Revenue": 5.0, "EV/EBITDA": 17.0, "P/E": 22.0},
            {"name": "C", "EV/Revenue": 30.0, "EV/EBITDA": 19.0, "P/E": 24.0},  # 30 > 4.5*2 异常
        ],
    }
    out3 = C.analyze(data3)
    assert "C" in out3["multiples"]["EV/Revenue"].get("outliers", []), "应标记 C 为 EV/Rev 异常值"

    print("✅ comps_calc 单测全部通过")
    return ok


if __name__ == "__main__":
    sys_exit = __import__("sys").exit
    sys_exit(0 if run() else 1)
