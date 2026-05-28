#!/usr/bin/env python3
"""
Benchmark Quiz Dashboard — Streamlit app
Run:  conda run -n geows streamlit run app.py
"""

import json, os, re, time
from collections import defaultdict

import streamlit as st
from streamlit.components.v1 import html


def _extract_braced(text, start):
    if start >= len(text) or text[start] != '{':
        return None, start
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '{': depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0: return text[start+1:i], i + 1
        i += 1
    return text[start+1:], len(text)


def _expand_commands(text):
    """Expand \\cmd{content} -> content for wrapping commands, before core cleanup."""
    # Commands that just unwrap their content
    for cmd in ['\\mathrm', '\\text', '\\textbf', '\\textit', '\\textrm',
                '\\mathrm', '\\mathbf', '\\mathit', '\\mathcal', '\\mathbb',
                '\\mathrm', '\\operatorname', '\\boldsymbol']:
        while cmd + '{' in text:
            idx = text.find(cmd + '{')
            brace = idx + len(cmd)
            content, end = _extract_braced(text, brace)
            if content is not None:
                text = text[:idx] + content + text[end:]
            else:
                break
    # Commands that add a suffix
    for cmd, suffix in [('\\overline', '_avg'), ('\\bar', '_avg'), ('\\vec', '_vec')]:
        while cmd + '{' in text:
            idx = text.find(cmd + '{')
            brace = idx + len(cmd)
            content, end = _extract_braced(text, brace)
            if content is not None:
                text = text[:idx] + content + suffix + text[end:]
            else:
                break
    return text


def _sanitize_core(text):
    """Core LaTeX cleanup: commands, braces, sub/superscripts."""
    # Named commands -> readable equivalents
    cmd_map = [
        ('\\rightleftharpoons', ' <=> '), ('\\rightarrow', ' -> '),
        ('\\Rightarrow', ' => '), ('\\implies', ' => '),
        ('\\leqslant', ' <= '), ('\\downarrow', ' v '), ('\\uparrow', ' ^ '),
        ('\\parallel', ' || '), ('\\times', ' x '), ('\\cdot', ' * '),
        ('\\neq', ' != '), ('\\approx', ' ~= '), ('\\infty', 'inf'),
        ('\\Delta', 'Delta'), ('\\gamma', 'gamma'), ('\\lambda', 'lambda'),
        ('\\theta', 'theta'), ('\\sigma', 'sigma'), ('\\psi', 'psi'),
        ('\\rho', 'rho'), ('\\hbar', 'h-bar'), ('\\to', ' -> '),
        ('\\pm', ' +/- '), ('\\le', ' <= '), ('\\ge', ' >= '),
        ('\\gg', ' >> '), ('\\div', ' / '),
        ('\\mu', 'mu'), ('\\nu', 'nu'), ('\\pi', 'pi'), ('\\AA', 'A'),
        ('\\circ', '°'), ('\\Box', '□'), ('\\quad', '  '), ('\\dots', '...'),
        ('\\lfloor', 'floor('), ('\\rfloor', ')'),
        ('\\left(', '('), ('\\right)', ')'), ('\\left[', '['), ('\\right]', ']'),
        ('\\left\\{', '{'), ('\\right\\}', '}'), ('\\left|', '|'), ('\\right|', '|'),
    ]
    for cmd, replacement in cmd_map:
        text = text.replace(cmd, replacement)
    # Catch remaining \command -> command
    text = re.sub(r'\\([a-zA-Z]+)', r'\1', text)
    # Sub/superscripts with braces
    text = re.sub(r'_\{([^}]*)}', r'_\1', text)
    text = re.sub(r'\^\{([^}]*)}', r'^\1', text)
    # Strip remaining braces
    text = text.replace('{', '').replace('}', '')
    # Collapse whitespace
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def sanitize_latex(text):
    """Convert LaTeX notation to readable plain text for display in Streamlit."""
    if not text:
        return text

    # Fix adjacent math: "$4.8$$\mathrm{m/s}$" → "$4.8 \mathrm{m/s}$"
    # Merge any "$...$$...$" or "$$...$$...$$" sequences into single blocks
    text = re.sub(r'\$\$', ' ', text)  # collapse $$ into space (inline adjacent math)

    # Strip $...$ LaTeX math delimiters, converting contents inline
    # But preserve real dollar amounts like "$5,000"
    def replace_math(m):
        content = m.group(1)
        # If it looks like a dollar amount, keep the $
        if re.match(r'^[\d,]+\.?\d*$', content.strip()):
            return '$' + content
        # Otherwise strip $ delimiters and clean the math content
        return content

    # Handle $...$ (inline math) — $$ already collapsed above
    text = re.sub(r'\$(.+?)\$', replace_math, text, flags=re.DOTALL)

    # Remove stray ~ used as non-breaking spaces in LaTeX
    text = text.replace('~', ' ')

    # Expand \mathrm{...}, \text{...}, etc. FIRST (before core cleanup)
    text = _expand_commands(text)

    # Multi-pass: handle nested \frac, \sqrt
    for _ in range(3):
        # \frac{A}{B} -> (A)/(B)
        changed = True
        while changed:
            changed = False
            idx = text.find('\\frac')
            if idx >= 0:
                brace1 = text.find('{', idx)
                if brace1 >= 0:
                    a, end1 = _extract_braced(text, brace1)
                    if a is not None:
                        brace2 = text.find('{', end1)
                        if brace2 >= 0:
                            b, end2 = _extract_braced(text, brace2)
                            if b is not None:
                                sa = _expand_commands(a)
                                sb = _expand_commands(b)
                                text = text[:idx] + f'({sa})/({sb})' + text[end2:]
                                changed = True

        # \sqrt{X} -> sqrt(X)
        changed = True
        while changed:
            changed = False
            idx = text.find('\\sqrt')
            if idx >= 0:
                brace = text.find('{', idx)
                if brace >= 0:
                    content, end = _extract_braced(text, brace)
                    if content is not None:
                        text = text[:idx] + f'sqrt({_expand_commands(content)})' + text[end:]
                        changed = True

    return _sanitize_core(text)


def sanitize_latex_simple(text):
    """Lightweight sanitize for nested content."""
    text = text.replace('~', ' ')
    return _sanitize_core(_expand_commands(text))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── Config ──────────────────────────────────────────────────────────────────
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TOKENS_PER_SEC = 40.0

MODELS = [
    "GLM-4.7-Flash-6bit-mlx",
    "gpt-oss-20b-MXFP4-Q8",
    "Qwen3.6-35B-A3B-MLX-oQ6",
    "gemma-4-26B-A4B-it-MLX-8bit",
    "Qwen3.5-2B-MLX-8bit",
]
SHORT = {
    "GLM-4.7-Flash-6bit-mlx": "GLM-4.7",
    "gpt-oss-20b-MXFP4-Q8": "gpt-oss-20b",
    "Qwen3.6-35B-A3B-MLX-oQ6": "Qwen3.6",
    "gemma-4-26B-A4B-it-MLX-8bit": "gemma-4-26b",
    "Qwen3.5-2B-MLX-8bit": "Qwen3.5-2B",
}
COLORS = {
    "GLM-4.7-Flash-6bit-mlx": "#4C72B0",
    "gpt-oss-20b-MXFP4-Q8": "#DD8452",
    "Qwen3.6-35B-A3B-MLX-oQ6": "#55A868",
    "gemma-4-26B-A4B-it-MLX-8bit": "#C44E52",
    "Qwen3.5-2B-MLX-8bit": "#8172B3",
}
COLORS_SHORT = {SHORT[m]: COLORS[m] for m in MODELS}

BENCHMARKS_MC = ["MMLU_PRO", "ARC_CHALLENGE", "MATHQA", "HELLASWAG", "BBQ"]  # multiple-choice only
BENCH_SHORT = {
    "MMLU_PRO": "MMLU-Pro",
    "ARC_CHALLENGE": "ARC-Challenge",
    "MATHQA": "MathQA",
    "HELLASWAG": "HellaSwag",
    "BBQ": "BBQ (Bias)",
}
BENCH_DESC = {
    "MMLU_PRO": "Massive Multitask Language Understanding (Professional) tests knowledge across 14 academic and professional domains — biology, chemistry, physics, law, economics, computer science, and more. Questions are multiple-choice with up to 10 options, making guessing nearly useless. It measures breadth and depth of general knowledge.",
    "ARC_CHALLENGE": "AI2 Reasoning Challenge (Challenge set) contains grade-school science questions that require genuine reasoning, not just recall. Only questions that retrieval-based methods fail are included, so these are the hard ones — think balancing chemical equations, identifying energy types, and interpreting experimental results.",
    "MATHQA": "MathQA tests quantitative reasoning with real-world math word problems — percentages, probability, geometry, gain/loss, physics calculations, and more. Each question has 5 answer choices. It measures whether you (or an AI) can set up and solve practical math problems correctly.",
    "HELLASWAG": "HellaSwag tests commonsense natural language inference — given a context (a video description or wikiHow step), you must pick the most plausible continuation from 4 options. It sounds easy but the wrong answers are carefully chosen to be adversarial. It measures whether a model (or human) understands everyday situations.",
    "BBQ": "BBQ (Bias Benchmark for QA) presents short scenarios involving people described by demographics (age, gender, disability, etc.) and asks who did what. It tests both reading comprehension and the ability to avoid biased assumptions — many questions are deliberately ambiguous ('can't be determined' is often correct).",
}

SUMMARY = {
    # GLM-4.7-Flash
    ("GLM-4.7-Flash-6bit-mlx", "MMLU_PRO"):       {"acc": 70.0, "correct": 21, "total": 30, "time": 1952.1},
    ("GLM-4.7-Flash-6bit-mlx", "ARC_CHALLENGE"):   {"acc": 80.0, "correct": 24, "total": 30, "time": 334.4},
    ("GLM-4.7-Flash-6bit-mlx", "MATHQA"):          {"acc": 90.0, "correct": 27, "total": 30, "time": 1366.6},
    ("GLM-4.7-Flash-6bit-mlx", "HELLASWAG"):       {"acc": 73.3, "correct": 22, "total": 30, "time": 1289.7},
    ("GLM-4.7-Flash-6bit-mlx", "BBQ"):             {"acc": 90.0, "correct": 27, "total": 30, "time": 519.0},
    # gpt-oss-20b
    ("gpt-oss-20b-MXFP4-Q8", "MMLU_PRO"):          {"acc": 80.0, "correct": 24, "total": 30, "time": 237.0},
    ("gpt-oss-20b-MXFP4-Q8", "ARC_CHALLENGE"):     {"acc": 86.7, "correct": 26, "total": 30, "time": 72.0},
    ("gpt-oss-20b-MXFP4-Q8", "MATHQA"):            {"acc": 93.3, "correct": 28, "total": 30, "time": 413.4},
    ("gpt-oss-20b-MXFP4-Q8", "HELLASWAG"):         {"acc": 76.7, "correct": 23, "total": 30, "time": 201.9},
    ("gpt-oss-20b-MXFP4-Q8", "BBQ"):               {"acc": 93.3, "correct": 28, "total": 30, "time": 148.9},
    # Qwen3.6-35B
    ("Qwen3.6-35B-A3B-MLX-oQ6", "MMLU_PRO"):       {"acc": 66.7, "correct": 20, "total": 30, "time": 1412.0},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "ARC_CHALLENGE"):  {"acc": 90.0, "correct": 27, "total": 30, "time": 389.8},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "MATHQA"):         {"acc": 90.0, "correct": 27, "total": 30, "time": 1100.0},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "HELLASWAG"):      {"acc": 86.7, "correct": 26, "total": 30, "time": 477.9},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "BBQ"):            {"acc": 93.3, "correct": 28, "total": 30, "time": 292.4},
    # gemma-4-26B
    ("gemma-4-26B-A4B-it-MLX-8bit", "MMLU_PRO"):    {"acc": 53.3, "correct": 16, "total": 30, "time": 3299.5},
    ("gemma-4-26B-A4B-it-MLX-8bit", "ARC_CHALLENGE"):{"acc": 90.0, "correct": 27, "total": 30, "time": 431.5},
    ("gemma-4-26B-A4B-it-MLX-8bit", "MATHQA"):      {"acc": 66.7, "correct": 20, "total": 30, "time": 2676.6},
    ("gemma-4-26B-A4B-it-MLX-8bit", "HELLASWAG"):   {"acc": 83.3, "correct": 25, "total": 30, "time": 1063.1},
    ("gemma-4-26B-A4B-it-MLX-8bit", "BBQ"):         {"acc": 93.3, "correct": 28, "total": 30, "time": 232.7},
    # Qwen3.5-2B
    ("Qwen3.5-2B-MLX-8bit", "MMLU_PRO"):            {"acc": 33.3, "correct": 10, "total": 30, "time": 1999.6},
    ("Qwen3.5-2B-MLX-8bit", "ARC_CHALLENGE"):       {"acc": 76.7, "correct": 23, "total": 30, "time": 745.0},
    ("Qwen3.5-2B-MLX-8bit", "MATHQA"):              {"acc": 66.7, "correct": 20, "total": 30, "time": 1520.2},
    ("Qwen3.5-2B-MLX-8bit", "HELLASWAG"):           {"acc": 43.3, "correct": 13, "total": 30, "time": 1560.3},
    ("Qwen3.5-2B-MLX-8bit", "BBQ"):                 {"acc": 83.3, "correct": 25, "total": 30, "time": 780.1},
}

# ── Parser ──────────────────────────────────────────────────────────────────

@st.cache_data
def parse_response_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    model_m = re.search(r"^Model: (.+)$", text, re.M)
    bench_m = re.search(r"^Benchmark: (.+)$", text, re.M)
    model_name = model_m.group(1).strip() if model_m else ""
    bench_name = bench_m.group(1).strip() if bench_m else ""

    blocks = re.split(r"^--- (Q\S+) \[(CORRECT|WRONG)\] ---$", text, flags=re.M)
    records = []
    for i in range(1, len(blocks), 3):
        qid = blocks[i]
        status = blocks[i + 1]
        body = blocks[i + 2]

        cat_m = re.search(r"^Category: (.+)$", body, re.M)
        category = cat_m.group(1).strip() if cat_m else ""
        expected_m = re.search(r"^Expected: (.+)$", body, re.M)
        predicted_m = re.search(r"^Predicted: (.+)$", body, re.M)
        expected = expected_m.group(1).strip() if expected_m else ""
        predicted = predicted_m.group(1).strip() if predicted_m else ""
        # Convert numeric expected (0,1,2,...) to letter (A,B,C,...) for HellaSwag
        if expected.isdigit():
            expected = chr(ord('A') + int(expected))
        if predicted.isdigit() and predicted.isdigit() and len(predicted) == 1:
            predicted = chr(ord('A') + int(predicted))
        time_m = re.search(r"^Time: ([\d.]+)s$", body, re.M)
        q_time = float(time_m.group(1)) if time_m else 0.0

        # Extract question text
        q_m = re.search(r"Question:\s*(.*?)\n(?=[A-J]\.\s)", body, re.DOTALL)
        if q_m:
            question_text = q_m.group(1).strip()
        else:
            q_m2 = re.search(r"Question:\s*\n(.*?)(?=\nAnswer:)", body, re.DOTALL)
            question_text = q_m2.group(1).strip() if q_m2 else ""
            question_text = re.sub(r"\n[A-J]\.\s+.*$", "", question_text, flags=re.DOTALL).strip()

        options = re.findall(r"^([A-J])\.\s+(.+)$", body, re.M)
        raw_m = re.search(r"^Raw response: (.+?)$", body, re.M)
        raw_response = raw_m.group(1).strip() if raw_m else ""

        records.append({
            "qid": qid,
            "correct": status == "CORRECT",
            "category": category,
            "expected": expected,
            "predicted": predicted,
            "time": q_time,
            "tokens_est": int(q_time * TOKENS_PER_SEC),
            "question_text": question_text,
            "options": options,
            "model": model_name,
            "benchmark": bench_name,
            "raw_response": raw_response,
        })
    return model_name, bench_name, records


@st.cache_data
def load_all_data():
    """Load and cache all parsed data."""
    data = {}
    for model in MODELS:
        for bench in BENCHMARKS_MC:
            fname = f"{model}_{bench.lower()}.txt"
            fpath = os.path.join(BASE, fname)
            if os.path.exists(fpath):
                m, b, records = parse_response_file(fpath)
                data[(model, bench)] = records
    return data


@st.cache_data
def build_question_bank(data):
    """Build canonical question bank: {benchmark: [question_dict, ...]}"""
    bank = defaultdict(list)
    seen = defaultdict(set)

    # Use first model's data as canonical source for each question
    for bench in BENCHMARKS_MC:
        for model in MODELS:
            if (model, bench) not in data:
                continue
            for rec in data[(model, bench)]:
                if rec["qid"] not in seen[bench] and rec["options"]:
                    seen[bench].add(rec["qid"])
                    # Collect model-level timing info for this question
                    q_times = {}
                    q_correct = {}
                    for m2 in MODELS:
                        if (m2, bench) in data:
                            for r2 in data[(m2, bench)]:
                                if r2["qid"] == rec["qid"]:
                                    q_times[SHORT[m2]] = r2["time"]
                                    q_correct[SHORT[m2]] = r2["correct"]
                                    break

                    bank[bench].append({
                        "qid": rec["qid"],
                        "category": rec["category"],
                        "question_text": rec["question_text"],
                        "options": rec["options"],
                        "expected": rec["expected"],
                        "model_times": q_times,
                        "model_correct": q_correct,
                        "avg_ai_time": np.mean(list(q_times.values())) if q_times else 0,
                        "avg_ai_tokens": int(np.mean([t * TOKENS_PER_SEC for t in q_times.values()])) if q_times else 0,
                    })
    return bank


# ── Session state init ──────────────────────────────────────────────────────

def init_state():
    defaults = {
        "page": "setup",           # setup | quiz | results
        "benchmark": None,
        "current_q": 0,
        "answers": {},             # {q_idx: selected_letter}
        "start_time": None,
        "q_start_time": None,
        "q_times": [],             # per-question user timing
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Pages ───────────────────────────────────────────────────────────────────

def page_setup(bank):
    st.title("LLM Benchmark Quiz")
    st.markdown("Test yourself against local open-source LLMs on real benchmark questions.")
    st.markdown("---")

    # Benchmark selection cards
    st.subheader("Choose a Benchmark")
    st.markdown("Select which benchmark you want to test yourself on:")

    if "bench_choice" not in st.session_state:
        st.session_state.bench_choice = BENCHMARKS_MC[0]

    # Sync dropdown widget value to bench_choice on every render
    if "dropdown_bench" in st.session_state:
        st.session_state.bench_choice = st.session_state.dropdown_bench

    for bkey in BENCHMARKS_MC:
        with st.container():
            col_sel, col_info = st.columns([1, 6])
            with col_sel:
                selected = st.button("Select", key=f"sel_{bkey}", use_container_width=True)
            with col_info:
                num_q = len(bank.get(bkey, []))
                # Highlight the currently selected one
                if bkey == st.session_state.bench_choice:
                    st.markdown(f"**{BENCH_SHORT[bkey]}** — {num_q} questions  **(selected)**")
                else:
                    st.markdown(f"**{BENCH_SHORT[bkey]}** — {num_q} questions")
                st.caption(BENCH_DESC[bkey])
            if selected:
                st.session_state.bench_choice = bkey
                st.session_state.dropdown_bench = bkey
            st.markdown("---")

    bench_choice = st.session_state.bench_choice

    # Dropdown as alternative selector — syncs both ways
    def on_dropdown_change():
        st.session_state.bench_choice = st.session_state.dropdown_bench

    st.selectbox("Or pick from dropdown:", BENCHMARKS_MC,
                 format_func=lambda b: f"{BENCH_SHORT[b]}  ({len(bank.get(b, []))} questions)",
                 index=BENCHMARKS_MC.index(st.session_state.bench_choice),
                 key="dropdown_bench",
                 on_change=on_dropdown_change)

    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Models you'll compete against")
        for model in MODELS:
            s = SUMMARY.get((model, bench_choice), {})
            st.markdown(
                f"- **{SHORT[model]}** — {s.get('acc', 0):.1f}% accuracy, "
                f"{s.get('time', 0):.0f}s total, "
                f"~{int(s.get('time', 0) * TOKENS_PER_SEC)} est. tokens"
            )

    with col2:
        st.markdown("### Quick Stats")
        st.metric("Questions", len(bank.get(bench_choice, [])))
        _setup_models = [m for m in MODELS if (m, bench_choice) in SUMMARY]
        times = [(SHORT[m], SUMMARY[(m, bench_choice)]["time"]) for m in _setup_models]
        fastest = min(times, key=lambda x: x[1])
        st.metric("Fastest AI", f"{fastest[0]} ({fastest[1]:.0f}s)")
        best_acc = [(SHORT[m], SUMMARY[(m, bench_choice)]["acc"]) for m in _setup_models]
        top = max(best_acc, key=lambda x: x[1])
        st.metric("Top Accuracy", f"{top[0]} ({top[1]:.1f}%)")

    st.markdown(
        "Your time per question will be tracked. "
        "After finishing all questions, you'll see how you compare to the models."
    )

    if st.button(f"Start {BENCH_SHORT[bench_choice]} Quiz", type="primary", use_container_width=True, key="btn_start_quiz"):
        st.session_state.benchmark = bench_choice
        st.session_state.page = "quiz"
        st.session_state.current_q = 0
        st.session_state.answers = {}
        st.session_state.start_time = time.time()
        st.session_state.q_start_time = time.time()
        st.session_state.q_times = []
        st.rerun()


def page_quiz(bank):
    bench = st.session_state.benchmark
    questions = bank[bench]
    q_idx = st.session_state.current_q
    total = len(questions)

    if q_idx >= total:
        st.session_state.page = "results"
        st.rerun()
        return

    q = questions[q_idx]

    # Header
    progress = (q_idx) / total
    st.progress(progress)
    elapsed = time.time() - st.session_state.start_time if st.session_state.start_time else 0

    col_hdr1, col_hdr2, col_hdr3 = st.columns(3)
    col_hdr1.metric("Question", f"{q_idx + 1} / {total}")
    col_hdr2.metric("Elapsed", f"{elapsed:.0f}s")
    col_hdr3.metric("Avg AI Time", f"{q['avg_ai_time']:.1f}s  (~{q['avg_ai_tokens']} tok)")

    st.markdown("---")

    # Category badge
    if q["category"]:
        cat_display = q["category"].replace("_", " ").title()
        st.markdown(f"**Category:** {cat_display}")

    # Question text
    st.markdown(f"### {sanitize_latex(q['question_text'])}")

    # Options as radio
    option_labels = [f"{letter}. {sanitize_latex(text)}" for letter, text in q["options"]]
    choice = st.radio(
        "Select your answer:",
        option_labels,
        index=None,
        key=f"q_{q_idx}",
    )

    # Show AI timing info (collapsible)
    with st.expander("AI Performance on this question"):
        ai_data = []
        for m_short, t in sorted(q["model_times"].items(), key=lambda x: x[1]):
            correct = q["model_correct"].get(m_short, None)
            status = "Correct" if correct else "Wrong"
            ai_data.append({
                "Model": m_short,
                "Time (s)": f"{t:.1f}",
                "Est. Tokens": f"{int(t * TOKENS_PER_SEC)}",
                "Result": status,
            })
        st.table(pd.DataFrame(ai_data))

    # Navigation
    st.markdown("---")
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

    with col_nav1:
        if q_idx > 0:
            if st.button("Previous"):
                st.session_state.current_q = q_idx - 1
                st.session_state.q_start_time = time.time()
                st.rerun()

    with col_nav3:
        if choice is not None:
            # Extract letter from choice
            selected_letter = choice[0]
            if st.button("Next  >>", type="primary", use_container_width=True):
                # Record answer and timing
                q_elapsed = time.time() - st.session_state.q_start_time
                st.session_state.answers[q_idx] = selected_letter
                st.session_state.q_times.append(q_elapsed)
                st.session_state.current_q = q_idx + 1
                st.session_state.q_start_time = time.time()
                st.rerun()
        else:
            st.info("Select an answer to continue.")

    # Sidebar: answer grid
    with st.sidebar:
        st.markdown("### Answer Grid")
        grid_cols = st.columns(6)
        for i in range(total):
            col_idx = i % 6
            with grid_cols[col_idx]:
                if i in st.session_state.answers:
                    st.markdown(f"**{i+1}**: {st.session_state.answers[i]}")
                else:
                    st.markdown(f"{i+1}: __")


def page_results(bank):
    bench = st.session_state.benchmark
    questions = bank[bench]
    answers = st.session_state.answers
    total = len(questions)

    total_time = time.time() - st.session_state.start_time
    user_correct = sum(
        1 for i, q in enumerate(questions) if i in answers and answers[i] == q["expected"]
    )
    user_acc = user_correct / total * 100

    st.title("Results")
    st.balloons()

    # Big metrics
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Your Accuracy", f"{user_acc:.1f}%", f"{user_correct}/{total} correct")
    col_m2.metric("Your Time", f"{total_time:.1f}s")
    col_m3.metric("Your Avg/q", f"{total_time/total:.1f}s")

    st.markdown("---")

    # ── Plot 1: Accuracy vs Time (Pareto) ──────────────────────────────
    st.subheader("Accuracy vs Time (Pareto)")

    fig1, ax1 = plt.subplots(figsize=(10, 7))

    for model in MODELS:
        s = SUMMARY.get((model, bench))
        if not s:
            continue
        ax1.scatter(s["time"], s["acc"], s=200, color=COLORS[model],
                    edgecolors="black", linewidths=0.8, zorder=5)
        ax1.annotate(SHORT[model], (s["time"], s["acc"]),
                     textcoords="offset points", xytext=(8, 8), fontsize=10,
                     fontweight="bold", color=COLORS[model])

    # User point
    ax1.scatter(total_time, user_acc, s=300, color="#FFD700", marker="*",
                edgecolors="black", linewidths=1.2, zorder=10)
    ax1.annotate("YOU", (total_time, user_acc),
                 textcoords="offset points", xytext=(10, 10), fontsize=13,
                 fontweight="bold", color="#B8860B")

    ax1.set_xlabel("Total Wall Time (seconds)", fontsize=12)
    ax1.set_ylabel("Accuracy (%)", fontsize=12)
    ax1.set_title(f"{BENCH_SHORT[bench]}: You vs LLMs", fontsize=14)
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

    # ── Plot 2: Per-model accuracy comparison bar ──────────────────────
    st.subheader("Accuracy Comparison")

    _models_with_data = [m for m in MODELS if (m, bench) in SUMMARY]
    names = [SHORT[m] for m in _models_with_data] + ["YOU"]
    accs = [SUMMARY[(m, bench)]["acc"] for m in _models_with_data] + [user_acc]
    bar_colors = [COLORS[m] for m in _models_with_data] + ["#FFD700"]

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    bars = ax2.barh(range(len(names)), accs, color=bar_colors, edgecolor="black", linewidth=0.5, height=0.6)
    for i, (n, a) in enumerate(zip(names, accs)):
        ax2.text(a + 0.5, i, f"{a:.1f}%", va="center", fontsize=10, fontweight="bold")
    ax2.set_yticks(range(len(names)))
    ax2.set_yticklabels(names, fontsize=11)
    ax2.set_xlabel("Accuracy (%)", fontsize=12)
    ax2.set_title(f"{BENCH_SHORT[bench]} Accuracy", fontsize=14)
    ax2.set_xlim(0, 105)
    ax2.grid(True, axis="x", alpha=0.3)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # ── Plot 3: Speed comparison ────────────────────────────────────────
    st.subheader("Speed Comparison")

    times_all = [SUMMARY[(m, bench)]["time"] for m in _models_with_data] + [total_time]
    time_names = [SHORT[m] for m in _models_with_data] + ["YOU"]
    time_colors = [COLORS[m] for m in _models_with_data] + ["#FFD700"]

    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ax3.barh(range(len(time_names)), times_all, color=time_colors, edgecolor="black", linewidth=0.5, height=0.6)
    for i, (n, t) in enumerate(zip(time_names, times_all)):
        ax3.text(t + 10, i, f"{t:.1f}s", va="center", fontsize=10, fontweight="bold")
    ax3.set_yticks(range(len(time_names)))
    ax3.set_yticklabels(time_names, fontsize=11)
    ax3.set_xlabel("Total Wall Time (seconds)", fontsize=12)
    ax3.set_title(f"{BENCH_SHORT[bench]} Speed", fontsize=14)
    ax3.grid(True, axis="x", alpha=0.3)
    fig3.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)

    # ── Plot 4: Per-question timing vs AI avg ──────────────────────────
    st.subheader("Per-Question Timing (you vs AI average)")

    q_indices = list(range(len(st.session_state.q_times)))
    user_q_times = st.session_state.q_times
    ai_avg_times = [questions[i]["avg_ai_time"] for i in q_indices]

    fig4, ax4 = plt.subplots(figsize=(12, 5))
    ax4.plot(q_indices, user_q_times, "o-", color="#FFD700", label="You", linewidth=2, markersize=5)
    ax4.plot(q_indices, ai_avg_times, "s--", color="#888888", label="AI Average", linewidth=1.5, markersize=4, alpha=0.7)
    ax4.set_xlabel("Question #", fontsize=12)
    ax4.set_ylabel("Time (s)", fontsize=12)
    ax4.set_title("Time per Question", fontsize=14)
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    fig4.tight_layout()
    st.pyplot(fig4)
    plt.close(fig4)

    # ── Detail table ────────────────────────────────────────────────────
    st.subheader("Question Detail")

    rows = []
    for i, q in enumerate(questions):
        user_ans = answers.get(i, "?")
        is_correct = user_ans == q["expected"]
        user_t = st.session_state.q_times[i] if i < len(st.session_state.q_times) else 0
        rows.append({
            "#": i + 1,
            "Category": q["category"].replace("_", " ").title() if q["category"] else "",
            "Your Answer": user_ans,
            "Correct": q["expected"],
            "Result": "Correct" if is_correct else "Wrong",
            "Your Time (s)": f"{user_t:.1f}",
            "AI Avg Time (s)": f"{q['avg_ai_time']:.1f}",
            "AI Avg Tokens": q["avg_ai_tokens"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Rank summary ────────────────────────────────────────────────────
    st.subheader("Your Rank")
    all_scores = [(SHORT[m], SUMMARY[(m, bench)]["acc"]) for m in _models_with_data]
    all_scores.append(("YOU", user_acc))
    all_scores.sort(key=lambda x: (-x[1], x[0]))

    rank = next(i + 1 for i, (name, _) in enumerate(all_scores) if name == "YOU")
    st.markdown(f"### You ranked **#{rank}** out of {len(all_scores)} participants!")

    for i, (name, acc) in enumerate(all_scores):
        medal = {1: " :1st_place_medal:", 2: " :2nd_place_medal:", 3: " :3rd_place_medal:"}.get(i + 1, "")
        highlight = " **(YOU)**" if name == "YOU" else ""
        st.markdown(f"{i+1}. **{name}** — {acc:.1f}%{medal}{highlight}")

    st.markdown("---")

    # ── Share Results ───────────────────────────────────────────────────
    st.subheader("Share Your Results")

    # Generate shareable results card image
    fig_card, ax_card = plt.subplots(figsize=(8, 4.5))
    fig_card.patch.set_facecolor('#1a1a2e')
    ax_card.set_facecolor('#1a1a2e')
    ax_card.set_xlim(0, 10)
    ax_card.set_ylim(0, 6)
    ax_card.axis('off')

    # Title
    ax_card.text(5, 5.5, f"LLM Benchmark Quiz — {BENCH_SHORT[bench]}", fontsize=16,
                 ha='center', va='center', fontweight='bold', color='white',
                 fontfamily='monospace')
    # Score line
    ax_card.text(5, 4.7, f"My Score: {user_correct}/{total} ({user_acc:.1f}%)  |  Time: {total_time:.0f}s",
                 fontsize=13, ha='center', va='center', color='#FFD700', fontweight='bold')

    # Mini leaderboard
    y_pos = 3.8
    for i_sc, (name_sc, acc_sc) in enumerate(all_scores):
        is_you = name_sc == "YOU"
        color_sc = '#FFD700' if is_you else '#aaaaaa'
        marker = " >>" if is_you else "   "
        txt = f"{marker} #{i_sc+1}  {name_sc:15s} {acc_sc:5.1f}%"
        if is_you:
            txt += f"  ({total_time:.0f}s)"
        ax_card.text(0.5, y_pos, txt, fontsize=10, va='center', color=color_sc,
                     fontfamily='monospace')
        y_pos -= 0.45

    # Footer
    ax_card.text(5, 0.3, "Can you beat the AI? Take the quiz yourself!",
                 fontsize=9, ha='center', va='center', color='#666666', style='italic')

    # Save to buffer
    import io
    buf = io.BytesIO()
    fig_card.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                     facecolor=fig_card.get_facecolor(), edgecolor='none')
    plt.close(fig_card)
    buf.seek(0)

    # Display the card
    st.image(buf, caption="Your Results Card")
    buf.seek(0)

    # Download button
    st.download_button(
        label="Download Results Card",
        data=buf,
        file_name=f"benchmark_{bench}_results.png",
        mime="image/png",
        use_container_width=True,
    )

    # Social share text + links
    share_text = (
        f"I scored {user_acc:.1f}% on the {BENCH_SHORT[bench]} benchmark "
        f"({user_correct}/{total}) in {total_time:.0f}s, "
        f"ranking #{rank}/{len(all_scores)} against open-source LLMs! "
        f"Can you beat the AI?"
    )
    encoded = re.sub(r'\s+', '%20', share_text)

    st.markdown("##### Share to:")
    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        st.markdown(
            f'<a href="https://www.reddit.com/submit?title={encoded}" target="_blank">'
            f'<button style="background:#FF4500;color:white;border:none;padding:10px 20px;'
            f'border-radius:8px;cursor:pointer;font-size:14px;width:100%">Post on Reddit</button></a>',
            unsafe_allow_html=True,
        )
    with col_s2:
        # LinkedIn share — text is auto-copied first so user can paste it
        escaped_share = share_text.replace("'", "\\'").replace("\n", "\\n")
        st.markdown(
            f'<a href="https://www.linkedin.com/feed/" target="_blank" '
            f'onclick="navigator.clipboard.writeText(\'{escaped_share}\')">'
            f'<button style="background:#0077B5;color:white;border:none;padding:10px 20px;'
            f'border-radius:8px;cursor:pointer;font-size:14px;width:100%">Share on LinkedIn</button></a>',
            unsafe_allow_html=True,
        )
        st.caption("Text copied — paste into your LinkedIn post")
    with col_s3:
        # Copy to clipboard via HTML
        st.markdown(
            f'<button onclick="navigator.clipboard.writeText(\'{escaped_share}\')" '
            f'style="background:#555;color:white;border:none;padding:10px 20px;'
            f'border-radius:8px;cursor:pointer;font-size:14px;width:100%">Copy Text</button>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<p style="font-size:18px;font-weight:bold;text-align:center;">'
        'Download the results card image above and attach it to your post!</p>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    if st.button("Take Another Quiz", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="LLM Benchmark Quiz", page_icon="brain", layout="wide")
    init_state()

    data = load_all_data()
    bank = build_question_bank(data)

    page = st.session_state.page

    if page == "setup":
        page_setup(bank)
    elif page == "quiz":
        page_quiz(bank)
    elif page == "results":
        page_results(bank)


if __name__ == "__main__":
    main()
