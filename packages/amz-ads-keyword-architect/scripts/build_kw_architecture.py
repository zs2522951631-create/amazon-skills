#!/usr/bin/env python3
"""Build an Amazon keyword expansion workbook from a keyword CSV.

The script is stdlib-only. It preserves input columns and appends practical
Amazon keyword expansion fields for Listing and PPC usage.
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import re
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path


KEYWORD_COLUMNS = [
    "关键词",
    "keyword",
    "search term",
    "search_term",
    "customer search term",
    "query",
    "term",
]

APPEND_COLUMNS = [
    "规范关键词",
    "词类",
    "相关性",
    "优先级",
    "Listing用途",
    "PPC用途",
    "否词风险",
    "备注",
]

MATERIAL_WORDS = {
    "wood",
    "wooden",
    "plastic",
    "metal",
    "stainless",
    "silicone",
    "cotton",
    "leather",
    "bamboo",
    "glass",
    "ceramic",
    "aluminum",
}

ATTRIBUTE_WORDS = {
    "small",
    "large",
    "mini",
    "xl",
    "thick",
    "thin",
    "wide",
    "narrow",
    "portable",
    "foldable",
    "compact",
    "heavy duty",
    "lightweight",
    "waterproof",
    "non slip",
    "nonslip",
    "rechargeable",
    "wireless",
    "corded",
    "cordless",
    "electric",
    "manual",
    "adjustable",
    "washable",
    "replacement",
    "compatible",
}

SCENARIO_WORDS = {
    "for home",
    "home",
    "office",
    "travel",
    "camping",
    "outdoor",
    "indoor",
    "kitchen",
    "bathroom",
    "bedroom",
    "garage",
    "car",
    "gift",
    "christmas",
    "halloween",
    "wedding",
    "storage",
}

AUDIENCE_WORDS = {
    "kids",
    "children",
    "baby",
    "toddler",
    "teen",
    "women",
    "men",
    "adult",
    "senior",
    "beginner",
    "professional",
    "pet",
    "dog",
    "cat",
}

PAIN_WORDS = {
    "pain",
    "bad knees",
    "back pain",
    "easy install",
    "odor",
    "noise",
    "quiet",
    "leak",
    "scratch",
    "non slip",
    "nonslip",
}


def split_terms(value: str) -> list[str]:
    return [part.strip().lower() for part in re.split(r"[,;\n]", value or "") if part.strip()]


def normalize(text: str) -> str:
    text = (text or "").replace("\ufeff", " ")
    text = re.sub(r"\s+", " ", text.strip())
    return text


def word_parts(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def phrase_present(text: str, phrase: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])"
    return bool(re.search(pattern, text.lower()))


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    sample = raw[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(raw), dialect=dialect)
    headers = list(reader.fieldnames or [])
    rows = [{k or "": v or "" for k, v in row.items()} for row in reader]
    return headers, rows


def find_keyword_column(headers: list[str], requested: str | None) -> str:
    if requested:
        if requested not in headers:
            raise SystemExit(f"Keyword column not found: {requested}")
        return requested
    lookup = {header.strip().lower(): header for header in headers}
    for candidate in KEYWORD_COLUMNS:
        if candidate in lookup:
            return lookup[candidate]
    raise SystemExit("No keyword column found. Use --keyword-column.")


def classify_keyword(
    keyword: str,
    core_terms: list[str],
    brand_terms: list[str],
    competitor_brands: list[str],
    conflict_terms: list[str],
    source: str,
) -> tuple[str, str, str, str, str, str, str]:
    kw = keyword.lower()
    words = set(word_parts(kw))
    source_l = source.lower()

    conflict_hits = [term for term in conflict_terms if phrase_present(kw, term)]
    own_brand_hits = [term for term in brand_terms if phrase_present(kw, term)]
    competitor_hits = [term for term in competitor_brands if phrase_present(kw, term)]
    core_hits = [term for term in core_terms if phrase_present(kw, term)]

    if conflict_hits:
        return (
            "否词候选",
            "低",
            "P3",
            "不建议埋词",
            "否定候选",
            "属性冲突",
            f"命中排除/冲突词：{', '.join(conflict_hits)}。",
        )
    if own_brand_hits:
        return ("品牌词", "高", "P0", "标题/五点", "精准", "无", "命中自有品牌词，适合防守和品牌承接。")
    if competitor_hits:
        return ("竞品词", "中", "P2", "后台 Search Terms", "低价测试", "品牌风险", "命中竞品品牌词，投放前确认合规和预算。")

    if "review" in source_l or "voc" in source_l:
        keyword_type = "Review/VOC词"
    elif core_hits and len(words) <= 3:
        keyword_type = "核心大词"
    elif core_hits and len(words) >= 4:
        keyword_type = "长尾词"
    elif any(phrase_present(kw, term) for term in PAIN_WORDS):
        keyword_type = "痛点词"
    elif any(phrase_present(kw, term) for term in SCENARIO_WORDS):
        keyword_type = "场景词"
    elif any(phrase_present(kw, term) for term in AUDIENCE_WORDS):
        keyword_type = "人群词"
    elif words & MATERIAL_WORDS or any(phrase_present(kw, term) for term in ATTRIBUTE_WORDS):
        keyword_type = "属性词"
    elif any(word in words for word in {"for", "compatible", "fits", "fit"}):
        keyword_type = "适配词"
    else:
        keyword_type = "待人工确认"

    if core_hits and keyword_type in {"核心大词", "长尾词", "属性词", "场景词", "痛点词", "人群词", "Review/VOC词"}:
        relevance = "高"
    elif core_hits or keyword_type in {"属性词", "场景词", "痛点词", "人群词", "适配词", "Review/VOC词"}:
        relevance = "中"
    else:
        relevance = "待人工确认"

    if keyword_type == "核心大词" and relevance == "高":
        priority = "P0"
        listing = "标题"
        ppc = "精准"
    elif relevance == "高":
        priority = "P1"
        listing = "五点/后台 Search Terms"
        ppc = "精准/词组"
    elif relevance == "中":
        priority = "P2"
        listing = "描述/A+或后台 Search Terms"
        ppc = "低价测试"
    else:
        priority = "P3"
        listing = "待人工确认"
        ppc = "暂不投放"

    if keyword_type == "待人工确认":
        note = "未命中核心词或明确属性，需要结合产品画像人工复核。"
    elif core_hits:
        note = f"命中核心词：{', '.join(core_hits)}；按{keyword_type}处理。"
    else:
        note = f"按语义识别为{keyword_type}，需结合 ASIN 画像确认相关性。"

    return keyword_type, relevance, priority, listing, ppc, "无", note


def enrich_rows(rows: list[dict[str, str]], keyword_col: str, args: argparse.Namespace) -> list[dict[str, str]]:
    core_terms = split_terms(args.core_terms) or split_terms(args.product_name)
    brand_terms = split_terms(args.brand_terms)
    competitor_brands = split_terms(args.competitor_brands)
    conflict_terms = split_terms(args.conflict_terms)

    enriched = []
    seen: dict[str, dict[str, str]] = {}
    for row in rows:
        keyword = normalize(row.get(keyword_col, ""))
        if not keyword:
            continue
        normalized = keyword.lower() if args.lowercase_normalized else keyword
        source = row.get("来源") or row.get("source") or args.source or "未标注"
        key = normalized.lower()
        if key in seen:
            existing = seen[key]
            sources = set(part.strip() for part in existing.get("来源", "").split(";") if part.strip())
            sources.add(source)
            existing["来源"] = "; ".join(sorted(sources))
            continue
        output = dict(row)
        output["关键词"] = keyword
        output["规范关键词"] = normalized
        output["来源"] = source
        (
            output["词类"],
            output["相关性"],
            output["优先级"],
            output["Listing用途"],
            output["PPC用途"],
            output["否词风险"],
            output["备注"],
        ) = classify_keyword(normalized, core_terms, brand_terms, competitor_brands, conflict_terms, source)
        seen[key] = output
        enriched.append(output)
    return enriched


def read_optional_csv(path_value: str) -> tuple[list[str], list[dict[str, str]]]:
    if not path_value:
        return [], []
    path = Path(path_value)
    if not path.exists():
        raise SystemExit(f"Optional CSV not found: {path}")
    return read_csv(path)


def col_name(index: int) -> str:
    name = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def sheet_xml(headers: list[str], rows: list[dict[str, str]]) -> str:
    all_rows = [headers] + [[str(row.get(header, "")) for header in headers] for row in rows]
    xml_rows = []
    for r_idx, values in enumerate(all_rows, start=1):
        cells = []
        for c_idx, value in enumerate(values):
            ref = f"{col_name(c_idx)}{r_idx}"
            escaped = html.escape(value, quote=False)
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escaped}</t></is></c>')
        xml_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>'
        + "".join(xml_rows)
        + "</sheetData></worksheet>"
    )


def emit_sheets_json(path: Path, sheets: list[tuple[str, list[str], list[dict[str, str]]]]) -> None:
    """Dump the exact same sheet set as a channel-agnostic JSON manifest.

    Feeds the 飞书 (Feishu) native-build delivery path: each entry's `headers`
    maps to `lark-cli sheets +create --headers` / a sheet's first row, and
    `rows` (2D string array) maps directly to `+append --values`. `values`
    is the convenience concatenation (header row + data rows) for a single
    `+append` that writes the whole tab in one call.
    """
    manifest = []
    for name, headers, rows in sheets:
        data_rows = [[str(row.get(h, "")) for h in headers] for row in rows]
        manifest.append({
            "name": name[:31],
            "headers": headers,
            "rows": data_rows,
            "values": [headers] + data_rows,
        })
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def write_xlsx(path: Path, sheets: list[tuple[str, list[str], list[dict[str, str]]]]) -> None:
    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    ]
    for idx in range(1, len(sheets) + 1):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{idx}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    content_types.append("</Types>")

    workbook_sheets = []
    workbook_rels = []
    for idx, (name, _, _) in enumerate(sheets, start=1):
        safe_name = html.escape(name[:31], quote=True)
        workbook_sheets.append(f'<sheet name="{safe_name}" sheetId="{idx}" r:id="rId{idx}"/>')
        workbook_rels.append(
            f'<Relationship Id="rId{idx}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{idx}.xml"/>'
        )

    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{"".join(workbook_sheets)}</sheets></workbook>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(workbook_rels)
        + "</Relationships>"
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "".join(content_types))
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        for idx, (_, headers, rows) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml(headers, rows))


def count_sheet(rows: list[dict[str, str]], column: str, first_header: str) -> list[dict[str, str]]:
    counts = Counter(row.get(column, "-") or "-" for row in rows)
    return [{first_header: key, "关键词数": str(value)} for key, value in counts.most_common()]


def build_instruction_sheet(args: argparse.Namespace, row_count: int) -> list[dict[str, str]]:
    return [
        {"项目": "生成日期", "内容": date.today().isoformat()},
        {"项目": "产品", "内容": args.product_name or "未填写"},
        {"项目": "核心词", "内容": args.core_terms or "未填写"},
        {"项目": "数据说明", "内容": "脚本仅做启发式分类；搜索量、排名、点击份额等指标必须来自外部数据，不得虚构。"},
        {"项目": "下游说明", "内容": "VOC库/收录排名追踪为待填脚手架；指标列默认『待检测/待数据验证』，由分析人结合工具取数后回填，禁止编造。"},
        {"项目": "行数", "内容": str(row_count)},
    ]


# ---------------------------------------------------------------------------
# 下游资产化 Sheet（VOC词库 / 收录排名追踪，落 Excel）
# ---------------------------------------------------------------------------

VOC_HEADERS = ["口语关键词/短语", "语义维度", "对应标准搜索表达", "证据片段", "建议用途", "状态", "备注"]
TRACKING_HEADERS = [
    "检查日期", "ASIN", "关键词", "层级", "应用位置", "广告组/活动", "收录状态",
    "自然排名", "广告排名", "搜索量/需求", "CPC/成本", "ACOS", "订单", "风险状态",
    "动作建议", "下次复查日",
]
def build_voc_sheet(enriched: list[dict[str, str]], voc_path: str) -> list[dict[str, str]]:
    """优先用 --voc-csv；读取失败/为空则优雅回退到自动种词脚手架（证据片段留待填，不编造）。"""
    if voc_path:
        try:
            _, voc_rows = read_optional_csv(voc_path)
        except SystemExit:
            print(f"[warn] --voc-csv 读取失败，回退自动种词脚手架：{voc_path}")
            voc_rows = []
        if voc_rows:
            return voc_rows
    seeds = [
        row for row in enriched
        if row.get("词类") == "Review/VOC词"
        or "voc" in (row.get("来源", "").lower())
        or "review" in (row.get("来源", "").lower())
    ]
    return [
        {
            "口语关键词/短语": row.get("关键词", ""),
            "语义维度": "待分类（正向场景/属性卖点/痛点风险/FAQ/否词）",
            "对应标准搜索表达": "待映射",
            "证据片段": "待填（Review/QA 原文，≤20 词，禁止编造）",
            "建议用途": "映射后再入主词库或 A+/FAQ；痛点仅进 FAQ/风险/否词",
            "状态": "待映射",
            "备注": f"来源：{row.get('来源', '未标注')}",
        }
        for row in seeds
    ]


def build_tracking_sheet(enriched: list[dict[str, str]], asin: str) -> list[dict[str, str]]:
    """从 P0/P1/P2 词派生收录排名追踪脚手架；所有指标列=待检测/待数据验证，绝不预填数值。"""
    rows: list[dict[str, str]] = []
    for row in enriched:
        priority = row.get("优先级", "")
        if priority not in {"P0", "P1", "P2"}:
            continue
        recheck = "周复查" if priority in {"P0", "P1"} else "低频复查（双周/月）"
        rows.append({
            "检查日期": "",
            "ASIN": asin or "待填",
            "关键词": row.get("关键词", ""),
            "层级": priority,
            "应用位置": row.get("Listing用途", ""),
            "广告组/活动": "待填",
            "收录状态": "待检测",
            "自然排名": "待检测",
            "广告排名": "待检测",
            "搜索量/需求": "待数据验证",
            "CPC/成本": "待数据验证",
            "ACOS": "待数据验证",
            "订单": "待数据验证",
            "风险状态": "待评估",
            "动作建议": "待填",
            "下次复查日": recheck,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an Amazon keyword expansion workbook.")
    parser.add_argument("input", help="Input keyword CSV.")
    parser.add_argument("-o", "--output", help="Output .xlsx path.")
    parser.add_argument("--keyword-column", help="Keyword column name. Defaults to auto-detection.")
    parser.add_argument("--product-name", default="", help="Product name.")
    parser.add_argument("--core-terms", default="", help="Comma-separated core terms.")
    parser.add_argument("--brand-terms", default="", help="Comma-separated own brand terms.")
    parser.add_argument("--competitor-brands", default="", help="Comma-separated competitor brand terms.")
    parser.add_argument("--conflict-terms", default="", help="Comma-separated conflict or negative terms.")
    parser.add_argument("--source", default="", help="Default source label.")
    parser.add_argument("--asin-summary", default="", help="Optional ASIN summary CSV.")
    parser.add_argument("--clusters-csv", default="", help="Optional ad-group cluster CSV.")
    parser.add_argument("--architecture-csv", default="", help="Optional ad campaign architecture CSV.")
    parser.add_argument("--voc-csv", default="", help="Optional VOC vocabulary CSV; else seeded from VOC/Review keywords.")
    parser.add_argument("--asin", default="", help="Own ASIN used to seed the ranking-tracking sheet.")
    parser.add_argument("--no-downstream", action="store_true", help="Skip VOC/tracking sheets.")
    parser.add_argument("--emit-sheets-json", default="", help="Also dump all sheets as a JSON manifest for 飞书 native-build delivery (lark-cli sheets).")
    parser.add_argument("--lowercase-normalized", action="store_true", help="Lowercase normalized keywords.")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    if input_path.suffix.lower() != ".csv":
        raise SystemExit("Input must be .csv")

    headers, rows = read_csv(input_path)
    keyword_col = find_keyword_column(headers, args.keyword_column)
    enriched = enrich_rows(rows, keyword_col, args)

    output_headers = list(headers)
    if "关键词" not in output_headers:
        output_headers.insert(0, "关键词")
    if "来源" not in output_headers:
        output_headers.append("来源")
    for column in APPEND_COLUMNS:
        if column not in output_headers:
            output_headers.append(column)

    asin_headers, asin_rows = read_optional_csv(args.asin_summary)
    output_path = Path(args.output) if args.output else input_path.with_name(f"amazon_keyword_expansion_{date.today().strftime('%Y%m%d')}.xlsx")
    if output_path.suffix.lower() != ".xlsx":
        raise SystemExit(f"Output must end with .xlsx: {output_path}")

    negative_rows = [row for row in enriched if row.get("否词风险") != "无" or row.get("词类") == "否词候选"]
    # CHECKPOINT 2 机制护栏：否词池为空必须显式告警，不静默 exit 0
    if not negative_rows:
        print(
            "[warn] 否词候选为空，违反 CHECKPOINT 2「否词池非空」——"
            "请确认是否漏传 --conflict-terms / --competitor-brands，或确属无否词。"
        )

    sheets: list[tuple[str, list[str], list[dict[str, str]]]] = [
        ("拓词总表", output_headers, enriched),
        ("P0-P1优先词", output_headers, [row for row in enriched if row.get("优先级") in {"P0", "P1"}]),
        ("Listing埋词建议", output_headers, [row for row in enriched if row.get("Listing用途") != "不建议埋词"]),
        ("PPC投放建议", output_headers, [row for row in enriched if row.get("PPC用途") not in {"否定候选", "暂不投放"}]),
        ("否词候选", output_headers, negative_rows),
        ("来源汇总", ["来源", "关键词数"], count_sheet(enriched, "来源", "来源")),
        ("执行说明", ["项目", "内容"], build_instruction_sheet(args, len(enriched))),
    ]
    if asin_rows:
        sheets.insert(6, ("ASIN画像", asin_headers, asin_rows))

    if args.clusters_csv:
        c_headers, c_rows = read_optional_csv(args.clusters_csv)
        if c_headers:
            sheets.append(("主题簇", c_headers, c_rows))
    if args.architecture_csv:
        a_headers, a_rows = read_optional_csv(args.architecture_csv)
        if a_headers:
            sheets.append(("广告架构", a_headers, a_rows))

    # 下游资产化 Sheet（VOC词库 / 收录排名追踪，落 Excel）
    if not args.no_downstream:
        sheets.append(("VOC词库", VOC_HEADERS, build_voc_sheet(enriched, args.voc_csv)))
        sheets.append(("收录排名追踪", TRACKING_HEADERS, build_tracking_sheet(enriched, args.asin)))

    write_xlsx(output_path, sheets)

    if args.emit_sheets_json:
        json_path = Path(args.emit_sheets_json)
        if json_path.suffix.lower() != ".json":
            raise SystemExit(f"--emit-sheets-json must end with .json: {json_path}")
        emit_sheets_json(json_path, sheets)

    print(f"Input rows: {len(rows)}")
    print(f"Output rows: {len(enriched)}")
    print(f"Keyword column: {keyword_col}")
    print(f"Output: {output_path}")
    if args.emit_sheets_json:
        print(f"Sheets JSON: {args.emit_sheets_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
