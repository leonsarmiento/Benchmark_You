# Benchmark You

An interactive quiz dashboard where you test yourself against 11 open-source LLMs on real benchmark questions. Deployed on [Streamlit Cloud](https://streamlit.io/cloud).

> Benchmarks were made possible thanks to **omlx** developed by [Jundot](https://github.com/jundot/omlx) — a tool for running and evaluating LLMs locally on Apple Silicon via MLX.

## How It Works

1. **Pick a benchmark** — each comes with a short description so you know what to expect
2. **Answer 30 questions** — multiple choice, just like the AI did
3. **Get your results** — see how you rank against 11 models on accuracy, speed, and per-question performance
4. **Share your score** — download a results card or post to Reddit / LinkedIn

## Benchmarks

| Benchmark | Type | Description |
|-----------|------|-------------|
| MMLU-Pro | MC (up to 10) | Knowledge across 14 academic & professional domains |
| MMLU | MC (4) | Classic 57-subject academic knowledge test (10 models) |
| ARC-Challenge | MC (4) | Grade-school science reasoning |
| MathQA | MC (5) | Quantitative math word problems |
| HellaSwag | MC (4) | Commonsense natural language inference |
| BBQ | MC (3) | Bias benchmark for question answering |
| TruthfulQA | MC (4) | Truthfulness vs common misconceptions |
| WinoGrande | MC (2) | Coreference resolution / commonsense |
| SafetyBench | MC (4) | Safety awareness (privacy, bias, ethics) |

## Models You Compete Against

| Model | Size | Thinking |
|-------|------|----------|
| Qwen3-30B-MegaScience | 30B (MoE) | Yes |
| Huihui-Qwen3.6-35B-A3B | 35B (MoE) | Yes |
| Qwen3.6-35B-A3B | 35B (MoE) | Yes |
| GLM-4.7-Flash | — | Yes |
| gemma-4-26B-A4B-it | 26B | Yes |
| gpt-oss-20b | 20B | Yes |
| gemma-4-E4B-it | 4B | Yes |
| Qwen3.5-2B | 2B | Yes |
| Assistant_Pepe_8B | 8B | No |
| Llama-3.3-8B-Abliterated | 8B | No |
| Hypnos-i1-8B | 8B | No |

All models were run locally on Apple Silicon via MLX. Thinking models at ~40 tok/s; non-thinking models are much faster.

## AI Results

```
                    MegaScience  Huihui  Qwen3.6  GLM-4.7  gemma-4-26b  gpt-oss  gemma-4-E4B  Qwen3.5-2B  Pepe-8B  Llama3.3  Hypnos
MMLU-Pro               73.3%    70.0%    66.7%    70.0%    53.3%    80.0%     76.7%      33.3%      40.0%    36.7%    30.0%
ARC-Challenge          86.7%    93.3%    90.0%    80.0%    90.0%    86.7%     86.7%      76.7%      70.0%    66.7%    63.3%
MathQA                 90.0%    90.0%    90.0%    90.0%    66.7%    93.3%     93.3%      66.7%      43.3%    43.3%    30.0%
HellaSwag              86.7%    90.0%    86.7%    73.3%    83.3%    76.7%     70.0%      43.3%      66.7%    76.7%    73.3%
BBQ                    90.0%    90.0%    93.3%    90.0%    93.3%    93.3%     93.3%      83.3%      56.7%    73.3%    60.0%
TruthfulQA             93.3%    83.3%    96.7%    76.7%    80.0%    86.7%     66.7%      36.7%      46.7%    70.0%    56.7%
WinoGrande             73.3%    90.0%    86.7%    90.0%   100.0%    70.0%     83.3%      66.7%      63.3%    63.3%    40.0%
SafetyBench            83.3%    86.7%    86.7%    96.7%    93.3%    96.7%     83.3%      83.3%      93.3%    90.0%    83.3%
```

> **MMLU** (classic 4-option knowledge test) has results for **10 models** (29 questions — one defective source question excluded): Qwen3.6-27B 79.3%, Qwen3.5-9B 79.3%, Qwen3.5-2B 75.9%, GLM-4.7 72.4%, gpt-oss-20b 72.4%, Qwen3.6-35B 69.0%, gemma-4-E4B 69.0%, gemma-4-26b 65.5%, Nex-N2-mini 62.1%, Devstral-24B 41.4%. The gemma-4-26b / Nex / Qwen3.6-35B rows were run on a different quant than their other benchmarks.

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
├── data/               # 87 response files (11 models x 8 benchmarks, minus missing)
└── README.md
```

## Acknowledgments

- Benchmarks run using [omlx](https://github.com/jundot/omlx) by Jundot
- Data sourced from [MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro), [MMLU](https://huggingface.co/datasets/cais/mmlu), [ARC-Challenge](https://huggingface.co/datasets/allenai/ai2_arc), [MathQA](https://huggingface.co/datasets/allenai/math_qa), [HellaSwag](https://huggingface.co/datasets/rowan/hellaswag), [BBQ](https://huggingface.co/datasets/heegyu/bbq), [TruthfulQA](https://huggingface.co/datasets/truthful_qa), [WinoGrande](https://huggingface.co/datasets/winogrande), and [SafetyBench](https://huggingface.co/datasets/SafetyBench)
