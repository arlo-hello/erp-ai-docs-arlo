#!/usr/bin/env python3
"""
ERP 需求池 CSV 分析脚本。
用法: python scripts/analyze_requirements.py <需求CSV路径> [缺陷CSV路径]
输出: JSON 格式的分析结果到 stdout
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path


def parse_csv(filepath):
    """Parse Feishu-exported CSV with BOM handling."""
    rows = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def count_defect_links(req_rows):
    """Count how many defects are linked to each requirement."""
    per_req = []
    for r in req_rows:
        d = r.get('需求关联缺陷', '').strip()
        cnt = len([x for x in d.replace('\n', ',').split(',') if x.strip()]) if d else 0
        per_req.append(cnt)
    return per_req


def extract_keywords(text):
    """Extract requirement domain keywords."""
    patterns = {
        '订单/履约': r'订单|履约|fulfill|发货|签收|取消订单',
        '库存/仓库': r'库存|仓库|warehouse|inventory|入库|出库|调拨',
        '售后/RMA': r'售后|退货|退款|RMA|换货|补发|工单|ticket',
        '支付/财务': r'支付|付款|退款|财务|账单|发票|结算|对账',
        '对接/集成': r'对接|集成|同步|webhook|回调|推送|拉取|API|接口',
        '数据/报表': r'数据|报表|看板|dashboard|统计|分析|pipeline|model|BI',
        '权限/用户': r'权限|用户|角色|登录|注册|邀请|认证',
        '页面/UI': r'页面|UI|界面|展示|显示|样式|布局|文案|前端',
        '配置/规则': r'配置|规则|交运|定价|申报|税率|渠道|策略',
        '批量/定时': r'批量|定时|自动|cron|job|任务|脚本',
        '导入/导出': r'导入|导出|import|export|上传|下载|Excel|CSV',
        '性能/优化': r'性能|优化|加速|提速|慢|卡顿|超时',
    }
    matched = []
    for name, pat in patterns.items():
        if re.search(pat, text, re.IGNORECASE):
            matched.append(name)
    return matched


def analyze_requirements(req_path, defect_path=None):
    """Main analysis function."""
    req_rows = parse_csv(req_path)
    defect_rows = parse_csv(defect_path) if defect_path else []

    # --- Basic stats ---
    total_req = len(req_rows)
    status_dist = Counter(r.get('状态', '').strip() for r in req_rows)
    pri_dist = Counter(r.get('优先级', '').strip() for r in req_rows)
    type_dist = Counter(r.get('需求类型', '').strip() for r in req_rows)

    # --- Traceability ---
    defect_links = count_defect_links(req_rows)
    linked_count = sum(1 for d in defect_links if d > 0)
    total_linked_defects = sum(defect_links)
    traceability_rate = linked_count / total_req * 100 if total_req > 0 else 0

    # Top requirements by defect count
    top_defect_reqs = []
    for i, r in enumerate(req_rows):
        if defect_links[i] > 0:
            top_defect_reqs.append({
                'name': r.get('需求名称', '').strip()[:80],
                'defects': defect_links[i],
                'priority': r.get('优先级', '').strip(),
                'type': r.get('需求类型', '').strip(),
            })
    top_defect_reqs.sort(key=lambda x: -x['defects'])

    # --- Waste rate ---
    withdrawn_statuses = ('需求撤回', '无需处理')
    withdrawn = [r for r in req_rows if r.get('状态', '').strip() in withdrawn_statuses]
    waste_rate = len(withdrawn) / total_req * 100 if total_req > 0 else 0

    # Withdrawal by type
    type_withdrawal = {}
    for r in req_rows:
        t = r.get('需求类型', '').strip()
        s = r.get('状态', '').strip()
        if t not in type_withdrawal:
            type_withdrawal[t] = {'total': 0, 'withdrawn': 0}
        type_withdrawal[t]['total'] += 1
        if s in withdrawn_statuses:
            type_withdrawal[t]['withdrawn'] += 1

    # --- Keyword domain analysis ---
    domain_stats = {}
    for r in req_rows:
        text = (r.get('需求名称', '') + ' ' + r.get('需求描述', '')).lower()
        domains = extract_keywords(text)
        for d in domains:
            if d not in domain_stats:
                domain_stats[d] = {'total': 0, 'withdrawn': 0, 'linked_defects': 0}
            domain_stats[d]['total'] += 1
            if r.get('状态', '').strip() in withdrawn_statuses:
                domain_stats[d]['withdrawn'] += 1

    # Cross with defects if available
    for i, r in enumerate(req_rows):
        text = (r.get('需求名称', '') + ' ' + r.get('需求描述', '')).lower()
        domains = extract_keywords(text)
        for d in domains:
            if d in domain_stats and defect_links[i] > 0:
                domain_stats[d]['linked_defects'] += defect_links[i]

    # --- Monthly trend ---
    monthly = Counter()
    for r in req_rows:
        t = r.get('提交时间', '').strip()
        if t and len(t) >= 7:
            monthly[t[:7]] += 1

    # --- Priority x Defect ---
    pri_defect = {}
    for i, r in enumerate(req_rows):
        pri = r.get('优先级', '').strip() or '(空)'
        if pri not in pri_defect:
            pri_defect[pri] = {'total': 0, 'defects': 0, 'linked': 0}
        pri_defect[pri]['total'] += 1
        pri_defect[pri]['defects'] += defect_links[i]
        if defect_links[i] > 0:
            pri_defect[pri]['linked'] += 1

    # --- Risk assessment ---
    risk_items = []

    # High withdrawal rate types
    for t, stats in type_withdrawal.items():
        if stats['total'] >= 5:
            rate = stats['withdrawn'] / stats['total'] * 100
            if rate >= 15:
                risk_items.append({
                    'level': '🔴',
                    'category': '高撤回率',
                    'detail': f'{t}: {stats["withdrawn"]}/{stats["total"]} ({rate:.1f}%) 撤回',
                })

    # Low traceability
    if traceability_rate < 5:
        risk_items.append({
            'level': '🔴',
            'category': '追溯断裂',
            'detail': f'需求-缺陷追溯率仅 {traceability_rate:.1f}%（{linked_count}/{total_req}）',
        })

    # --- Compile result ---
    return {
        'meta': {
            'total_requirements': total_req,
            'total_defects': len(defect_rows),
            'analysis_time': '',
        },
        'quality': {
            'traceability_rate': round(traceability_rate, 1),
            'linked_requirements': linked_count,
            'total_linked_defects': total_linked_defects,
            'waste_rate': round(waste_rate, 1),
            'withdrawn_count': len(withdrawn),
        },
        'status_distribution': dict(status_dist.most_common()),
        'priority_distribution': dict(pri_dist.most_common()),
        'type_distribution': dict(type_dist.most_common()),
        'type_withdrawal': {t: {'total': s['total'], 'withdrawn': s['withdrawn'], 'rate': round(s['withdrawn']/s['total']*100, 1)}
                           for t, s in type_withdrawal.items()},
        'domain_stats': {d: {'total': s['total'], 'withdrawn': s['withdrawn'], 'defects': s['linked_defects']}
                        for d, s in sorted(domain_stats.items(), key=lambda x: -x[1]['total'])},
        'monthly_trend': dict(sorted(monthly.items())),
        'priority_defect': {p: {'total': d['total'], 'defects': d['defects'], 'linked': d['linked']}
                           for p, d in pri_defect.items()},
        'top_defect_requirements': top_defect_reqs[:15],
        'risks': risk_items,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python analyze_requirements.py <需求CSV> [缺陷CSV]", file=sys.stderr)
        sys.exit(1)

    req_path = sys.argv[1]
    defect_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(req_path).exists():
        print(f"文件不存在: {req_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_requirements(req_path, defect_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
