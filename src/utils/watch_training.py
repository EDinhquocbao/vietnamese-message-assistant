"""Màn hình theo dõi tiến độ huấn luyện, tự làm mới.

Đọc thanh tiến độ trong file log và loss trong checkpoints/*/trainer_state.json (lưu mỗi eval_steps).
Chạy:  python -m src.utils.watch_training --log outputs/logs/train_correction_vit5-base.log \
           --run_dir models/correction/vit5-base
"""
import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path

_PROGRESS = re.compile(r"(\d+)%\|[^|]*\|\s*(\d+)/(\d+) \[([\d:]+)<([\d:?]+),\s*([\d.]+)(it/s|s/it)\]")


def last_progress(log: Path):
    """Dòng tiến độ huấn luyện cuối cùng (bỏ qua thanh tiến độ của bước eval, có tổng bước nhỏ hơn)."""
    text = log.read_text(encoding="utf-8", errors="replace").replace("\r", "\n")
    matches = [m.groups() for m in _PROGRESS.finditer(text)]
    if not matches:
        return None
    total = max(int(m[2]) for m in matches)
    train = [m for m in matches if int(m[2]) == total]
    return train[-1]


def latest_state(run_dir: Path) -> dict | None:
    states = sorted((run_dir / "checkpoints").glob("checkpoint-*/trainer_state.json"),
                    key=lambda p: int(p.parent.name.split("-")[1]))
    if (run_dir / "train_summary.json").exists():
        return json.loads((run_dir / "train_summary.json").read_text(encoding="utf-8")) | {"done": True}
    return json.loads(states[-1].read_text(encoding="utf-8")) if states else None


def gpu_line() -> str:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                              "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5).stdout
        util, used, total, temp = [x.strip() for x in out.strip().split(",")]
        return f"GPU {util}% | VRAM {int(used) / 1024:.1f}/{int(total) / 1024:.1f} GB | {temp}°C"
    except Exception:
        return "GPU: không đọc được nvidia-smi"


def render(log: Path, run_dir: Path) -> str:
    lines = [f"Theo dõi huấn luyện: {run_dir}", f"Cập nhật lúc {time.strftime('%H:%M:%S')}", ""]
    prog = last_progress(log) if log.exists() else None
    if prog:
        pct, step, total, elapsed, eta, speed, unit = prog
        width = 40
        filled = int(width * int(step) / int(total))
        lines += [f"[{'#' * filled}{'.' * (width - filled)}] {pct}%  bước {step}/{total}",
                  f"Đã chạy {elapsed}  |  còn lại ~{eta}  |  {speed} {unit}"]
    else:
        lines += ["Chưa thấy thanh tiến độ trong log (đang nạp dữ liệu/mô hình?)"]
    lines += [gpu_line(), ""]

    state = latest_state(run_dir)
    history = (state or {}).get("log_history", [])
    train = [h for h in history if "loss" in h]
    evals = [h for h in history if "eval_loss" in h]
    if state and state.get("done"):
        lines += ["*** ĐÃ XONG ***", f"Val loss tốt nhất: {state['best_val']['eval_loss']:.4f}  ({state['minutes']} phút)", ""]
    if train:
        lines += ["Train loss (mỗi 100 bước, 8 lần gần nhất):"]
        lines += [f"  bước {h['step']:>5}  epoch {h['epoch']:.2f}  loss {float(h['loss']):.4f}  lr {float(h['learning_rate']):.2e}"
                  for h in train[-8:]]
    else:
        lines += ["Train loss: sẽ có sau checkpoint đầu tiên (mỗi 1000 bước)."]
    lines += [""]
    if evals:
        best = min(float(h["eval_loss"]) for h in evals)
        lines += ["Val loss:"]
        lines += [f"  bước {h['step']:>5}  {float(h['eval_loss']):.4f}{'  <- tốt nhất' if float(h['eval_loss']) == best else ''}"
                  for h in evals]
    lines += ["", f"Log: {log}", "Ctrl+C để đóng (không ảnh hưởng việc huấn luyện)."]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="outputs/logs/train_correction_vit5-base.log")
    ap.add_argument("--run_dir", default="models/correction/vit5-base")
    ap.add_argument("--interval", type=float, default=10)
    ap.add_argument("--once", action="store_true", help="in một lần rồi thoát")
    args = ap.parse_args()
    while True:
        screen = render(Path(args.log), Path(args.run_dir))
        if args.once:
            print(screen)
            return
        os.system("cls" if os.name == "nt" else "clear")
        print(screen, flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
