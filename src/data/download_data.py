"""Tải dữ liệu về data/raw/<tên>/<split>.jsonl

- Dataset có `files` trong config: tải từng file CSV theo URL (đã ghim commit).
- Còn lại: tải qua thư viện `datasets` từ Hugging Face (`hf_name`).

Chạy:  python -m src.data.download_data            (tải tất cả)
       python -m src.data.download_data --only vsec
"""
import argparse
import io
import json
import urllib.request
from pathlib import Path

import pandas as pd

from src.utils.text_utils import load_config


def download_files(name: str, spec: dict, out_dir: Path) -> dict:
    info = {"files": spec["files"], "license": spec.get("license"), "citation": spec.get("citation"), "splits": {}}
    for split, url in spec["files"].items():
        print(f"  - tải {url}")
        with urllib.request.urlopen(url, timeout=120) as resp:
            df = pd.read_csv(io.BytesIO(resp.read()), dtype=str, keep_default_na=False)
        df = df.loc[:, ~df.columns.str.startswith("Unnamed")]  # bỏ cột index thừa
        df = df[(df[spec["source_col"]].str.strip() != "") & (df[spec["target_col"]].str.strip() != "")]
        df.to_json(out_dir / f"{split}.jsonl", orient="records", lines=True, force_ascii=False)
        info["splits"][split] = {"rows": len(df), "columns": list(df.columns)}
        print(f"    {split}: {len(df):,} dòng, cột = {list(df.columns)}")
    return info


def download_hf(name: str, spec: dict, out_dir: Path) -> dict:
    from datasets import load_dataset

    ds = load_dataset(spec["hf_name"])  # DatasetDict
    info = {"hf_name": spec["hf_name"], "splits": {}}
    for split, data in ds.items():
        path = out_dir / f"{split}.jsonl"
        data.to_json(str(path), force_ascii=False)
        info["splits"][split] = {"rows": len(data), "columns": data.column_names}
        print(f"  - {split}: {len(data):,} dòng, cột = {data.column_names}")

    # Lưu thông tin dataset card (license, mô tả) nếu thư viện lấy được
    try:
        first = next(iter(ds.values()))
        info["license"] = first.info.license or None
        info["description"] = (first.info.description or "")[:1000]
    except Exception:
        pass
    return info


def download(name: str, cfg: dict) -> None:
    spec = cfg["datasets"][name]
    out_dir = Path(cfg["raw_dir"]) / name
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{name}] Đang tải ...")
    info = download_files(name, spec, out_dir) if spec.get("files") else download_hf(name, spec, out_dir)
    (out_dir / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{name}] Xong -> {out_dir}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/data.yaml")
    ap.add_argument("--only", default=None, help="tên một dataset trong config")
    args = ap.parse_args()

    cfg = load_config(args.config)
    for name in ([args.only] if args.only else list(cfg["datasets"])):
        download(name, cfg)
    print("Nhớ đọc dataset card để ghi lại license/điều kiện sử dụng (giai đoạn 1).")


if __name__ == "__main__":
    main()
