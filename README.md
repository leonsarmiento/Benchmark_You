# Benchmark You

An interactive quiz dashboard where you test yourself against open-source LLMs on real benchmark questions. Deployed on [Streamlit Cloud](https://streamlit.io/cloud).

> Benchmarks were made possible thanks to **omlx** developed by [Jundot](https://github.com/jundot/omlx) — a tool for running and evaluating LLMs locally on Apple Silicon via MLX.

## How It Works

1. **Pick a benchmark** — each comes with a short description so you know what to expect
2. **Answer 30 questions** — multiple choice, just like the AI did
3. **Get your results** — see how you rank against 5 models on accuracy, speed, and per-question performance
4. **Share your score** — download a results card or post to Reddit / LinkedIn

## Benchmarks

| Benchmark | Type | Description |
|-----------|------|-------------|
| MMLU-Pro | MC (10 choices) | Knowledge across 14 academic & professional domains |
| ARC-Challenge | MC (4 choices) | Grade-school science reasoning |
| MathQA | MC (5 choices) | Quantitative math word problems |
| HellaSwag | MC (4 choices) | Commonsense natural language inference |
| BBQ | MC (3 choices) | Bias benchmark for question answering |

## Models You Compete Against

| Model | Size | Quantization |
|-------|------|-------------|
| GLM-4.7-Flash | — | 6-bit MLX |
| gpt-oss-20b | 20B | MXFP4-Q8 |
| Qwen3.6-35B-A3B | 35B (MoE) | 6-bit MLX |
| gemma-4-26B-A4B-it | 26B | 8-bit MLX |
| Qwen3.5-2B | 2B | 8-bit MLX |

All models were run locally on Apple Silicon via MLX at ~40 tok/s. The 2B model is included as a baseline.

## AI Results

```
               GLM-4.7  gpt-oss  Qwen3.6  gemma-4  Qwen3.5-2B
MMLU-Pro        70.0%    80.0%    66.7%    53.3%     33.3%
ARC-Challenge   80.0%    86.7%    90.0%    90.0%     76.7%
MathQA          90.0%    93.3%    90.0%    66.7%     66.7%
HellaSwag       73.3%    76.7%    86.7%    83.3%     43.3%
BBQ             90.0%    93.3%    93.3%    93.3%     83.3%
```

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

This is the self-contained deployment folder for Streamlit Cloud. The full project (analysis scripts, plots, questionnaires) lives in the [main repository](../).

```
Benchmark_You/
├── app.py              # Streamlit application
├── requirements.txt    # Python dependencies
├── data/               # 25 response files (5 models x 5 benchmarks)
└── README.md
```

## Acknowledgments

- Benchmarks run using [omlx](https://github.com/jundot/omlx) by Jundot
- Data sourced from [MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro), [ARC-Challenge](https://huggingface.co/datasets/allenai/ai2_arc), [MathQA](https://huggingface.co/datasets/allenai/math_qa), [HellaSwag](https://huggingface.co/datasets/rowan/hellaswag), and [BBQ](https://huggingface.co/datasets/heegyu/bbq)
