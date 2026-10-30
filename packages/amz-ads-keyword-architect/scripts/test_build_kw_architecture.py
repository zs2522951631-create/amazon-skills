import subprocess, sys, zipfile, pathlib, re, json

SCRIPT = pathlib.Path(__file__).with_name("build_kw_architecture.py")

def _sheet_names(xlsx_path):
    z = zipfile.ZipFile(xlsx_path)
    wb = z.read("xl/workbook.xml").decode("utf-8")
    return re.findall(r'<sheet name="([^"]+)"', wb)

def test_clusters_and_architecture_sheets(tmp_path):
    kw = tmp_path / "kw.csv"
    kw.write_text("关键词\nthick yoga mat\nyoga mat for women\n", encoding="utf-8")
    clusters = tmp_path / "clusters.csv"
    clusters.write_text("主题簇,主属性维度,相关性,需求,词数\n厚度,属性,高,高,12\n", encoding="utf-8")
    arch = tmp_path / "arch.csv"
    arch.write_text("campaign,ad_group,匹配方式,预算占比,攻守测\nSP-核心,厚度,精准,30%,守\n", encoding="utf-8")
    out = tmp_path / "out.xlsx"
    r = subprocess.run([sys.executable, str(SCRIPT), str(kw),
                        "--product-name", "yoga mat", "--core-terms", "yoga mat",
                        "--clusters-csv", str(clusters), "--architecture-csv", str(arch),
                        "-o", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    names = _sheet_names(out)
    assert "主题簇" in names
    assert "广告架构" in names


def test_downstream_sheets_present(tmp_path):
    kw = tmp_path / "kw.csv"
    kw.write_text(
        "关键词,来源\nthick yoga mat,ABA\nyoga mat slips review,Review/VOC\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.xlsx"
    r = subprocess.run([sys.executable, str(SCRIPT), str(kw),
                        "--product-name", "yoga mat", "--core-terms", "yoga mat",
                        "--asin", "B0TESTASIN1", "-o", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    names = _sheet_names(out)
    assert set(names) == {
        "拓词总表",
        "P0-P1优先词",
        "Listing埋词建议",
        "PPC投放建议",
        "否词候选",
        "来源汇总",
        "执行说明",
        "VOC词库",
        "收录排名追踪",
    }


def test_voc_csv_missing_falls_back(tmp_path):
    kw = tmp_path / "kw.csv"
    kw.write_text("关键词,来源\nyoga mat slips review,Review/VOC\n", encoding="utf-8")
    out = tmp_path / "out.xlsx"
    r = subprocess.run([sys.executable, str(SCRIPT), str(kw),
                        "--core-terms", "yoga mat",
                        "--voc-csv", str(tmp_path / "does_not_exist.csv"),
                        "-o", str(out)], capture_output=True, text=True)
    # 缺失的 --voc-csv 不应让整个流程崩溃，而是优雅回退
    assert r.returncode == 0, r.stderr
    assert "回退自动种词" in (r.stdout + r.stderr)
    assert "VOC词库" in _sheet_names(out)


def test_no_downstream_flag_suppresses(tmp_path):
    kw = tmp_path / "kw.csv"
    kw.write_text("关键词\nthick yoga mat\n", encoding="utf-8")
    out = tmp_path / "out.xlsx"
    r = subprocess.run([sys.executable, str(SCRIPT), str(kw),
                        "--core-terms", "yoga mat", "--no-downstream",
                        "-o", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    names = _sheet_names(out)
    assert "VOC词库" not in names
    # 原有 Sheet 不受影响
    assert "拓词总表" in names


def test_empty_negative_pool_warns(tmp_path):
    # 无 --conflict-terms / --competitor-brands 且无命中 → 否词池空 → 必须告警，不静默
    kw = tmp_path / "kw.csv"
    kw.write_text("关键词\nthick yoga mat\nyoga mat for women\n", encoding="utf-8")
    out = tmp_path / "out.xlsx"
    r = subprocess.run([sys.executable, str(SCRIPT), str(kw),
                        "--core-terms", "yoga mat", "-o", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "否词候选为空" in (r.stdout + r.stderr), "空否词池应触发 CHECKPOINT 2 告警"


def test_emit_sheets_json_matches_xlsx(tmp_path):
    # 飞书通道：--emit-sheets-json 导出的 manifest 必须与 xlsx 页签一一对应，
    # 且 values = headers + rows（首行为表头，喂 lark-cli sheets +append）。
    kw = tmp_path / "kw.csv"
    kw.write_text("关键词,来源\nthick yoga mat,ABA\nyoga mat slips review,Review/VOC\n", encoding="utf-8")
    out = tmp_path / "out.xlsx"
    manifest = tmp_path / "out.sheets.json"
    r = subprocess.run([sys.executable, str(SCRIPT), str(kw),
                        "--core-terms", "yoga mat", "--asin", "B0TESTASIN1",
                        "--conflict-terms", "with stand",
                        "-o", str(out), "--emit-sheets-json", str(manifest)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert manifest.exists(), "manifest not written"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    json_names = [s["name"] for s in data]
    assert json_names == _sheet_names(out), "JSON sheet order/names must match xlsx"
    for s in data:
        assert s["values"][0] == s["headers"], "values 首行必须是表头"
        assert s["values"][1:] == s["rows"], "values 余下必须等于 rows"


def test_emit_sheets_json_rejects_non_json_suffix(tmp_path):
    kw = tmp_path / "kw.csv"
    kw.write_text("关键词\nthick yoga mat\n", encoding="utf-8")
    out = tmp_path / "out.xlsx"
    r = subprocess.run([sys.executable, str(SCRIPT), str(kw),
                        "--core-terms", "yoga mat", "-o", str(out),
                        "--emit-sheets-json", str(tmp_path / "bad.txt")],
                       capture_output=True, text=True)
    assert r.returncode != 0
    assert "must end with .json" in (r.stdout + r.stderr)


def test_negative_pool_present_no_warn(tmp_path):
    # 传了 --conflict-terms 且命中 → 否词池非空 → 不应告警
    kw = tmp_path / "kw.csv"
    kw.write_text("关键词\nthick yoga mat\nyoga mat with stand\n", encoding="utf-8")
    out = tmp_path / "out.xlsx"
    r = subprocess.run([sys.executable, str(SCRIPT), str(kw),
                        "--core-terms", "yoga mat", "--conflict-terms", "with stand",
                        "-o", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "否词候选为空" not in (r.stdout + r.stderr)
