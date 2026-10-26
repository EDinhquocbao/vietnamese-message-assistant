
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

Data pipeline:

```bash
python -m src.data.download_data
python -m src.data.preprocess_vsec --all
python -m src.data.preprocess_visp
python -m src.data.split_data
python -m src.data.build_correction_mix
```

Please check each dataset's license and usage terms before use.

## Project Structure

- `configs/`: experiment configurations
- `data/`: raw and processed datasets
- `notebooks/`: exploratory analysis
- `src/data/`: data processing
- `src/correction/`: spelling correction
- `src/paraphrase/`: sentence rephrasing
- `src/pipeline/`: integrated pipeline
- `app/`: demo application
- `tests/`: unit tests
- `reports/`: figures and tables

## Setup

```bash
python -m venv .venv
```
