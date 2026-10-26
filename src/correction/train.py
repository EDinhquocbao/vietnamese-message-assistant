"""Fine-tune mô hình seq2seq sửa lỗi trên tập gộp data/processed/correction/.

Dùng chung cho diễn đạt lại (src.paraphrase.train gọi main với configs/paraphrase.yaml).

Chạy:  python -m src.correction.train                                   (theo configs/correction.yaml)
       python -m src.correction.train --max_train_samples 2000 --epochs 1 --output_dir models/correction/smoke
Mô hình tốt nhất (theo val loss) được lưu ở output_dir, kèm train_summary.json.
Đánh giá trên từng tập test bằng:  python -m src.correction.evaluate --model <output_dir> --data ...
"""
import argparse
import json
import time
from pathlib import Path

from transformers import (
    AutoModelForSeq2SeqLM, DataCollatorForSeq2Seq, Seq2SeqTrainer, Seq2SeqTrainingArguments,
)

from src.correction.dataset import build_dataset, load_pairs, load_tokenizer
from src.utils.seed import set_seed
from src.utils.text_utils import load_config


def main(default_config: str = "configs/correction.yaml"):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=default_config)
    ap.add_argument("--max_train_samples", type=int, default=None)
    ap.add_argument("--epochs", type=float, default=None)
    ap.add_argument("--output_dir", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    d, t = cfg["data"], cfg["train"]
    out_dir = Path(args.output_dir or cfg["output_dir"])
    epochs = args.epochs or t["epochs"]
    set_seed(cfg["seed"])

    tok = load_tokenizer(cfg["model_name"])
    model = AutoModelForSeq2SeqLM.from_pretrained(cfg["model_name"])

    train_df = load_pairs(d["train"], args.max_train_samples or d["max_train_samples"], cfg["seed"])
    val_df = load_pairs(d["val"], d["max_val_samples"], cfg["seed"])
    train_ds, train_dropped = build_dataset(train_df, tok, d["max_source_len"], d["max_target_len"])
    val_ds, val_dropped = build_dataset(val_df, tok, d["max_source_len"], d["max_target_len"])
    print(f"train: {len(train_ds):,} cặp (bỏ {train_dropped} cặp quá dài); val: {len(val_ds):,} (bỏ {val_dropped})")

    targs = Seq2SeqTrainingArguments(
        output_dir=str(out_dir / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=t["batch_size"],
        per_device_eval_batch_size=t["batch_size"] * 2,
        gradient_accumulation_steps=t["grad_accum"],
        optim=t["optim"],
        learning_rate=t["learning_rate"],
        warmup_steps=t["warmup_ratio"],  # transformers 5: số < 1 được hiểu là tỉ lệ
        weight_decay=t["weight_decay"],
        lr_scheduler_type="linear",
        bf16=t["bf16"],
        gradient_checkpointing=t["gradient_checkpointing"],
        train_sampling_strategy="group_by_length",  # gom câu cùng độ dài để bớt padding
        eval_strategy="steps",
        eval_steps=t["eval_steps"],
        save_strategy="steps",
        save_steps=t["eval_steps"],
        save_total_limit=t["save_total_limit"],
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        logging_steps=t["logging_steps"],
        report_to="none",
        seed=cfg["seed"],
        dataloader_num_workers=0,  # Windows: worker con hay lỗi/chậm
    )
    trainer = Seq2SeqTrainer(
        model=model, args=targs, train_dataset=train_ds, eval_dataset=val_ds,
        data_collator=DataCollatorForSeq2Seq(tok, model=model), processing_class=tok,
    )
    start = time.time()
    result = trainer.train()
    final_eval = trainer.evaluate()

    trainer.save_model(str(out_dir))
    tok.save_pretrained(str(out_dir))
    summary = {
        "model_name": cfg["model_name"], "config": cfg, "epochs": epochs,
        "train_rows": len(train_ds), "train_dropped_too_long": train_dropped,
        "val_rows": len(val_ds), "train_metrics": result.metrics, "best_val": final_eval,
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "minutes": round((time.time() - start) / 60, 1),
        "log_history": trainer.state.log_history,
    }
    (out_dir / "train_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out_dir}  (val loss tốt nhất {final_eval['eval_loss']:.4f}, {summary['minutes']} phút)")


if __name__ == "__main__":
    main()
