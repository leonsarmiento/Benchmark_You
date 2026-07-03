# Benchmark You

An interactive quiz dashboard where you test yourself against 27 open-source LLMs on real benchmark questions. Deployed on [Streamlit Cloud](https://streamlit.io/cloud).

> Benchmarks were made possible thanks to **omlx** developed by [Jundot](https://github.com/jundot/omlx) — a tool for running and evaluating LLMs locally on Apple Silicon via MLX.

## How It Works

1. **Pick a benchmark** — each comes with a short description so you know what to expect
2. **Answer 10 questions** — multiple choice, just like the AI did. Each attempt randomly samples 10 questions from the benchmark's pool (HPL uses all 10 of its own).
3. **Get your results** — see how you rank against 27 models on accuracy, speed, and per-question performance
4. **Share your score** — download a results card or post to Reddit / LinkedIn

## Benchmarks

| Benchmark | Type | Description |
|-----------|------|-------------|
| HPL | MC (2–5) | Husk-Phi-Leon — custom social-intelligence benchmark (uses all 10 of its own) |
| MMLU-Pro | MC (up to 10) | Knowledge across 14 academic & professional domains |
| MMLU | MC (4) | Classic 57-subject academic knowledge test (18 of 27 models) |
| ARC-Challenge | MC (4) | Grade-school science reasoning |
| MathQA | MC (5) | Quantitative math word problems |
| HellaSwag | MC (4) | Commonsense natural language inference |
| BBQ | MC (3) | Bias benchmark for question answering |
| TruthfulQA | MC (4) | Truthfulness vs common misconceptions |
| WinoGrande | MC (2) | Coreference resolution / commonsense |
| SafetyBench | MC (4) | Safety awareness (privacy, bias, ethics) |

## Models You Compete Against

27 models across 13 families. Grouped by family — MoE models marked with active-param count.

| Family | Models |
|--------|--------|
| Qwen3.5 | Qwen3.5-2B, Qwen3.5-4B, Qwen3.5-9B, Qwen3.5-35B-A3B, Nex-N2-mini, Ornith-1.0-35B, Ornith-1.0-9B, Agents-A1 |
| Qwen3.6 | Qwen3.6-27B, Huihui-Qwen3.6-35B, Qwen3.6-35B-A3B |
| Qwen3 | MegaScience-30B, Qwen3-Coder-30B, MechaEpstein-8B |
| Qwen2.5 | VibeThinker-3B |
| Gemma | gemma-4-E4B, gemma-4-26B-A4B |
| GLM | GLM-4.6V-Flash, GLM-4.7-Flash |
| GPT-OSS | gpt-oss-20b |
| Pepe | Pepe-8B, Pepe-32B |
| Llama | Llama-3.3-8B |
| Nemotron | Nemotron-30B |
| Devstral | Devstral-24B |
| Hypnos | Hypnos-8B |
| Domyn | Domyn-Small-10B |

All models run locally on Apple Silicon via MLX. Thinking models at ~40 tok/s; non-thinking models are much faster.

**Excluded:** Nemotron-3-Nano-Omni (full multimodal: text + audio + image) was benchmarked but left out of all comparisons — it isn't comparable to the text-only and text-image models in this suite. Its raw artifacts remain in the main repo for reference only.

## AI Results

Full per-model results across all benchmarks are in the [main repository README](../README.md#results-summary). Top scorers per benchmark:

| Benchmark | Best model(s) | Score |
|-----------|---------------|-------|
| HPL | Pepe-32B / Qwen3.5-9B / VibeThinker-3B / gpt-oss-20b | 50.0% |
| MMLU-Pro | Nemotron-30B / Nex-N2-mini / Qwen3.6-35B-A3B | 86.7% |
| MMLU | Qwen3.6-27B / Qwen3.5-9B | 79.3% |
| ARC-Challenge | Qwen3.6-27B | 93.3% |
| MathQA | Agents-A1 / Ornith-35B / Qwen3.6-35B-A3B / VibeThinker-3B | 96.7% |
| HellaSwag | Qwen3.5-9B | 90.0% |
| BBQ | Qwen3.5-9B | 96.7% |
| TruthfulQA | Agents-A1 / Ornith-35B / Qwen3.6-27B | 100.0% |
| WinoGrande | Qwen3.6-27B / gemma-4-26B-A4B | 86.7% |
| SafetyBench | GLM-4.7 / Nex-N2-mini / gpt-oss-20b | 96.7% |
| HumanEval | gemma-4-26B-A4B | 96.7% |
| MBPP | Qwen3.6-27B / gpt-oss-20b / Qwen3.6-35B-A3B / gemma-4-E4B | 86.7% |

> **MMLU** (classic) has results for **18 of 27** models (29 questions — one defective source question excluded). **HumanEval & MBPP** (code generation, non-thinking mode) cover **16 models**. MMLU-Pro, MathQA, and HPL are run in reasoning mode for thinking models; the other MC benchmarks use instruct mode (see main README methodology).

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
├── data/               # ~265 response files (27 models × MC benchmarks, minus missing)
└── README.md
```

## Adding a New Model

The full workflow (re-extraction, HPL, plot regeneration, verification, README updates) lives in the [main repository README](../README.md#scoring-new-models) — follow that end to end. Dashboard-specific steps, all in `app.py`:

1. Append the model to the **`MODELS`** list (must equal the file prefix, e.g. `Agents-A1-5bit-XL-mlx`).
2. Add entries to **`SHORT`** and **`COLORS`**.
3. If MoE and the name lacks `A3B`/`A4B`/`E4B`/`E3B`, add **`MOE_MODELS.add("name")`** (dense models: skip).
4. Add a branch to **`_family()`** so it groups correctly.
5. Paste the corrected entries into **`SUMMARY`** (8 MC + HPL + optional MMLU / HumanEval / MBPP).
6. Copy the model's `<model>_*.txt` into **`data/`** (the per-question quiz view reads live from there).
7. Update this README's model table, best-scores table, and "N of M" counts.

> The dashboard recomputes per-question correctness from the raw responses in `data/` using the same `extract_answer()` used for scoring, so its quiz view matches the `SUMMARY` totals whenever both use the corrected values. A model in `MODELS`/`SUMMARY` whose response file is missing (or held in a stale cache) never shows a false 0% — it falls back to its overall `SUMMARY` accuracy. The data cache is keyed on a fingerprint of the `data/` dir (file list + mtimes), so adding or changing a response file reliably refreshes it.

In the results and live leaderboard, **YOU** always sorts to the top of its score bracket on ties (it ranks first among models with the same accuracy/speed), and is highlighted in the plots — other series are dimmed, while the user's Pareto point, bars, and timing line are drawn larger, bolder, and fully opaque.

## Acknowledgments

- Benchmarks run using [omlx](https://github.com/jundot/omlx) by Jundot
- Data sourced from [MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro), [MMLU](https://huggingface.co/datasets/cais/mmlu), [ARC-Challenge](https://huggingface.co/datasets/allenai/ai2_arc), [MathQA](https://huggingface.co/datasets/allenai/math_qa), [HellaSwag](https://huggingface.co/datasets/rowan/hellaswag), [BBQ](https://huggingface.co/datasets/heegyu/bbq), [TruthfulQA](https://huggingface.co/datasets/truthful_qa), [WinoGrande](https://huggingface.co/datasets/winogrande), and [SafetyBench](https://huggingface.co/datasets/SafetyBench)
