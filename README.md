
# Vietnamese Message Assistant

A Vietnamese NLP project for spelling correction and
semantic-preserving sentence rephrasing using Transformer models.

## Objectives

- Correct spelling errors in Vietnamese messages.
- Generate alternative phrasings while preserving meaning.
- Integrate correction and rephrasing into a simple demo.

## Datasets

- VSEC: https://huggingface.co/datasets/nguyenthanhasia/vsec-vietnamese-spell-correction
- ViSP: https://huggingface.co/datasets/ngwgsang/ViSP
- ViLexNorm (social-media normalization, human-annotated, CC BY-NC-SA 4.0): https://github.com/ngxtnhi/ViLexNorm
- VEC (LLM-labeled, training augmentation only; rows overlapping ViLexNorm are removed): https://huggingface.co/datasets/yammdd/vietnamese-error-correction-corpus

Please check each dataset's license and usage terms before use.

## Models

| Task | Model | Data |
|---|---|---|
| Correction (used by the demo) | `VietAI/vit5-base`, two-stage fine-tuning | stage 1: VSEC + ViLexNorm + VEC + 89k synthetic fast-typing errors; stage 2: real data only |
| Paraphrase | `VietAI/vit5-base` fine-tuned | ViSP |
| Ranking filters | `paraphrase-multilingual-MiniLM-L12-v2` (similarity), `mDeBERTa-v3-base-xnli` (NLI) | used as-is |

Results, comparisons and open items: `docs/improvement_plan.md` and section 14 of
`Plan_NLP_Sua_loi_va_goi_y_dien_dat_tieng_Viet.docx`.

## Usage

Run from the repository root with the virtual environment's Python (GPU with ~6 GB VRAM is enough):

```bash
# data
python -m src.data.download_data
python -m src.data.preprocess_vsec --all
python -m src.data.preprocess_visp
python -m src.data.split_data
python -m src.data.build_correction_mix
python -m src.data.augment_errors            # synthetic typing errors, train split only

# training
python -m src.correction.train                                       # stage 1 -> models/correction/vit5-base-aug
python -m src.correction.train --config configs/correction_stage2.yaml  # stage 2 -> models/correction/vit5-base-aug-ft
python -m src.paraphrase.train                                       # -> models/paraphrase/vit5-base
python -m src.utils.watch_training --log outputs/logs/<run>.log --run_dir models/<task>/<run>   # progress monitor

# evaluation
python -m src.correction.evaluate --model models/correction/vit5-base-aug-ft --data data/processed/vilexnorm/test.jsonl
python -m src.correction.stress_test --models copy models/correction/vit5-base-aug-ft   # per error type, top-1 / top-3
python -m src.paraphrase.evaluate --model models/paraphrase/vit5-base --max_samples 2000 --semantic
python -m src.pipeline.calibrate_nli
python -m src.pipeline.evaluate_integration --include_draft

# demo
streamlit run app/streamlit_app.py --server.address localhost
```

On Windows set `PYTHONIOENCODING=utf-8` when scripts print Vietnamese text.

## Project Structure

- `configs/`: data, training and pipeline configurations
- `data/`: raw and processed datasets (git-ignored)
- `docs/`: improvement plan and results tracker
- `src/data/`: download, cleaning, splitting, synthetic errors
- `src/correction/`: correction training, prediction, evaluation, stress test
- `src/paraphrase/`: paraphrase training, generation, evaluation
- `src/pipeline/`: candidate ranker, two-step assistant, integration evaluation
- `app/`: Streamlit demo
- `tests/`: unit tests (`python -m pytest -q`)
- `notebooks/`, `reports/`: exploration and data reports

## Setup

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```
