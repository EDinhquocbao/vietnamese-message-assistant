
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
