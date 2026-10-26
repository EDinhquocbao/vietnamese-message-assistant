"""Fine-tune mô hình diễn đạt lại trên ViSP (câu gốc -> câu đồng nghĩa).

Dùng lại vòng huấn luyện seq2seq của src.correction.train, chỉ khác config.
Chạy:  python -m src.paraphrase.train
       python -m src.paraphrase.train --max_train_samples 2000 --epochs 1 --output_dir models/paraphrase/smoke
"""
from src.correction.train import main

if __name__ == "__main__":
    main(default_config="configs/paraphrase.yaml")
