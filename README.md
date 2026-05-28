# LLM Benchmark Suite

Comparison of 5 open-source LLMs across 5 standard benchmarks, with interactive quiz dashboard and full analysis.

> Benchmarks were made possible thanks to **omlx** developed by [Jundot](https://github.com/jundot/omlx) — a tool for running and evaluating LLMs locally on Apple Silicon via MLX.

## Models Tested

| Model | Size | Quantization |
|-------|------|-------------|
| GLM-4.7-Flash | — | 6-bit MLX |
| gpt-oss-20b | 20B | MXFP4-Q8 |
| Qwen3.6-35B-A3B | 35B (MoE) | 6-bit MLX |
| gemma-4-26B-A4B-it | 26B | 8-bit MLX |
| Qwen3.5-2B | 2B | 8-bit MLX |

All models run locally via MLX on Apple Silicon. Token generation rate: ~40 tok/s.

## Benchmarks

| Benchmark | Questions | Type | Description |
|-----------|-----------|------|-------------|
| MMLU-Pro | 30 sampled | MC (10 choices) | Knowledge across 14 academic & professional domains |
| ARC-Challenge | 30 sampled | MC (4 choices) | Grade-school science reasoning |
| MathQA | 30 sampled | MC (5 choices) | Quantitative math word problems |
| HellaSwag | 30 sampled | MC (4 choices) | Commonsense natural language inference |
| BBQ | 30 sampled | MC (3 choices) | Bias benchmark for question answering |

## Results Summary

```
               GLM-4.7  gpt-oss  Qwen3.6  gemma-4  Qwen3.5-2B
MMLU-Pro        70.0%    80.0%    66.7%    53.3%     33.3%
ARC-Challenge   80.0%    86.7%    90.0%    90.0%     76.7%
MathQA          90.0%    93.3%    90.0%    66.7%     66.7%
HellaSwag       73.3%    76.7%    86.7%    83.3%     43.3%
BBQ             90.0%    93.3%    93.3%    93.3%     83.3%
```

**Key finding:** gpt-oss-20b is the Pareto-optimal model — top accuracy at the lowest wall time. The 2B Qwen model struggles especially on MMLU-Pro and HellaSwag, as expected for its size.

## Repository Structure

```
.
├── benchmark.txt                          # Raw benchmark output
├── analyze_benchmark.py                   # Analysis & plot generation script
├── plots/                                 # 13 analysis plots (PNG)
├── all_questions_for_google_forms.txt     # All questions + answer key
├── failed_questions.txt                   # Questions at least 1 model failed
├── failed_questions_answer_key.txt        # Answer key for failed questions
├── dashboard/
│   └── app.py                             # Streamlit quiz dashboard
└── *_mmlu_pro.txt                         # Per-model response files
    *_arc_challenge.txt
    *_mathqa.txt
    *_hellaswag.txt
    *_bbq.txt
```

## Analysis Plots

Run the analysis script to generate 13 plots:

```bash
python3 analyze_benchmark.py
```

Plots saved to `plots/`:

| # | Plot | Description |
|---|------|-------------|
| 01 | Radar | Accuracy per benchmark per model |
| 02 | Heatmap | Model x benchmark accuracy matrix |
| 03 | Grouped Bar | Side-by-side accuracy comparison |
| 04 | Stacked Bar | Total score by benchmark |
| 05 | Pareto (overall) | Accuracy vs total wall time |
| 06 | Pareto (per benchmark) | Multi-panel accuracy vs time |
| 07 | Speed Ranking | Total time, fastest to slowest |
| 08 | Avg Time/Q | Average seconds per question |
| 09 | Efficiency Bubble | Time vs accuracy (bubble = correct count) |
| 10 | Error Profile | Wrong answers stacked by benchmark |
| 11 | Category Heatmap | Accuracy by topic (MMLU-Pro & MathQA) |
| 12 | Consensus Failures | Questions all-correct / mixed / all-wrong |
| 13 | Difficulty Distribution | Histogram: how many models got each Q right |

## Interactive Quiz Dashboard

Test yourself against the models with a Streamlit web app.

```bash
cd dashboard
conda run -n geows streamlit run app.py
```

Features:
- Choose from 5 multiple-choice benchmarks (MMLU-Pro, ARC-Challenge, MathQA, HellaSwag, BBQ)
- Each benchmark has a description so you know what you're getting into
- Timed quiz with per-question tracking
- Collapsible AI performance comparison per question
- Results page with:
  - Pareto plot (you vs 5 models)
  - Accuracy & speed ranking
  - Per-question timing comparison
  - Full detail table with answer review
- Share results to Reddit, LinkedIn, or copy text
- Download results card image

## Questionnaires for Human Benchmarking

- `all_questions_for_google_forms.txt` — All unique questions with options and answer key. Suitable for Google Forms or similar.
- `failed_questions.txt` — Questions that at least one model got wrong, annotated with which models failed each.
- `failed_questions_answer_key.txt` — Compact answer key for failed questions.

## Dependencies

```bash
# Analysis script
pip install numpy matplotlib

# Dashboard (use conda env with streamlit)
conda activate geows  # or: pip install streamlit numpy matplotlib pandas
```

## Acknowledgments

- Benchmarks run using [omlx](https://github.com/jundot/omlx) by Jundot
- Data sourced from [MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro), [ARC-Challenge](https://huggingface.co/datasets/allenai/ai2_arc), [MathQA](https://huggingface.co/datasets/allenai/math_qa), [HellaSwag](https://huggingface.co/datasets/rowan/hellaswag), and [BBQ](https://huggingface.co/datasets/heegyu/bbq)
