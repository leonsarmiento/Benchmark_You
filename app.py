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
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
# For local dashboard: data lives in parent dir. For deployment: data/ subfolder
BASE = DATA_DIR if os.path.isdir(DATA_DIR) else os.path.dirname(APP_DIR)
TOKENS_PER_SEC = 40.0

MODELS = [
    "Qwen3-30B-A3B-MegaScience-8bit-mlx",
    "Huihui-Qwen3.6-35B-A3B-6bit-mlx",
    "Qwen3.5-35B-A3B-6bit-mlx",
    "Qwen3.6-35B-A3B-MLX-oQ6",
    "GLM-4.7-Flash-6bit-mlx",
    "gemma-4-26B-A4B-it-oQ6",
    "gpt-oss-20b-MXFP4-Q8",
    "Qwen3.5-2B-MLX-8bit",
    "Assistant_Pepe_8B-8bit-mlx",
    "Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx",
    "Hypnos-i1-8B-8bit-mlx",
    "gemma-4-E4B-it-MLX-8bit",
    "Qwen3-Coder-30B-A3B-Instruct-MLX-6bit",
]
SHORT = {
    "Qwen3-30B-A3B-MegaScience-8bit-mlx": "MegaScience",
    "Huihui-Qwen3.6-35B-A3B-6bit-mlx": "Huihui-Qwen3.6",
    "Qwen3.5-35B-A3B-6bit-mlx": "Qwen3.5-35B",
    "Qwen3.6-35B-A3B-MLX-oQ6": "Qwen3.6",
    "GLM-4.7-Flash-6bit-mlx": "GLM-4.7",
    "gemma-4-26B-A4B-it-oQ6": "gemma-4-26b",
    "gpt-oss-20b-MXFP4-Q8": "gpt-oss-20b",
    "Qwen3.5-2B-MLX-8bit": "Qwen3.5-2B",
    "Assistant_Pepe_8B-8bit-mlx": "Pepe-8B",
    "Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx": "Llama3.3-8B",
    "Hypnos-i1-8B-8bit-mlx": "Hypnos-8B",
    "gemma-4-E4B-it-MLX-8bit": "gemma-4-E4B",
    "Qwen3-Coder-30B-A3B-Instruct-MLX-6bit": "Qwen3-Coder",
}
COLORS = {
    "Qwen3-30B-A3B-MegaScience-8bit-mlx": "#1f77b4",
    "Huihui-Qwen3.6-35B-A3B-6bit-mlx": "#ff7f0e",
    "Qwen3.5-35B-A3B-6bit-mlx": "#98df8a",
    "Qwen3.6-35B-A3B-MLX-oQ6": "#2ca02c",
    "GLM-4.7-Flash-6bit-mlx": "#d62728",
    "gemma-4-26B-A4B-it-oQ6": "#9467bd",
    "gpt-oss-20b-MXFP4-Q8": "#8c564b",
    "Qwen3.5-2B-MLX-8bit": "#e377c2",
    "Assistant_Pepe_8B-8bit-mlx": "#7f7f7f",
    "Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx": "#bcbd22",
    "Hypnos-i1-8B-8bit-mlx": "#17becf",
    "gemma-4-E4B-it-MLX-8bit": "#aec7e8",
    "Qwen3-Coder-30B-A3B-Instruct-MLX-6bit": "#dbdb8d",
}
COLORS_SHORT = {SHORT[m]: COLORS[m] for m in MODELS}

BENCHMARKS_MC = ["MMLU_PRO", "ARC_CHALLENGE", "MATHQA", "HELLASWAG", "BBQ", "TRUTHFULQA", "WINOGRANDE", "SAFETYBENCH"]
BENCH_SHORT = {
    "MMLU_PRO": "MMLU-Pro",
    "ARC_CHALLENGE": "ARC-Challenge",
    "MATHQA": "MathQA",
    "HELLASWAG": "HellaSwag",
    "BBQ": "BBQ (Bias)",
    "TRUTHFULQA": "TruthfulQA",
    "WINOGRANDE": "WinoGrande",
    "SAFETYBENCH": "SafetyBench",
}
BENCH_DESC = {
    "MMLU_PRO": "Massive Multitask Language Understanding (Professional) tests knowledge across 14 academic and professional domains - biology, chemistry, physics, law, economics, computer science, and more. Questions are multiple-choice with up to 10 options, making guessing nearly useless. It measures breadth and depth of general knowledge.",
    "ARC_CHALLENGE": "AI2 Reasoning Challenge (Challenge set) contains grade-school science questions that require genuine reasoning, not just recall. Only questions that retrieval-based methods fail are included, so these are the hard ones - think balancing chemical equations, identifying energy types, and interpreting experimental results.",
    "MATHQA": "MathQA tests quantitative reasoning with real-world math word problems - percentages, probability, geometry, gain/loss, physics calculations, and more. Each question has 5 answer choices. It measures whether you (or an AI) can set up and solve practical math problems correctly.",
    "HELLASWAG": "HellaSwag tests commonsense natural language inference - given a context (a video description or wikiHow step), you must pick the most plausible continuation from 4 options. It sounds easy but the wrong answers are carefully chosen to be adversarial. It measures whether a model (or human) understands everyday situations.",
    "BBQ": "BBQ (Bias Benchmark for QA) presents short scenarios involving people described by demographics (age, gender, disability, etc.) and asks who did what. It tests both reading comprehension and the ability to avoid biased assumptions - many questions are deliberately ambiguous.",
    "TRUTHFULQA": "TruthfulQA measures whether a model generates truthful answers to questions that humans commonly get wrong due to misconceptions, myths, and popular but false beliefs. Questions span health, law, finance, politics, and more. Many wrong answers sound very plausible - it tests actual knowledge, not confidence.",
    "WINOGRANDE": "WinoGrande is a coreference resolution benchmark - you read a sentence with a blank and decide which of two options fills it. It sounds simple but requires deep understanding of context, common sense, and social situations. Inspired by Winograd Schemas but at much larger scale.",
    "SAFETYBENCH": "SafetyBench evaluates safety awareness across categories like privacy, unfairness, bias, toxicity, and ethics. Questions present scenarios and ask you to identify risks, violations, or appropriate behaviors. It measures whether an AI (or human) can recognize and avoid harmful outputs.",
}
SUMMARY = {
    # Qwen3-30B-MegaScience
    ("Qwen3-30B-A3B-MegaScience-8bit-mlx", "MMLU_PRO"):       {"acc": 73.3, "correct": 22, "total": 30, "time": 351.8},
    ("Qwen3-30B-A3B-MegaScience-8bit-mlx", "HELLASWAG"):      {"acc": 86.7, "correct": 26, "total": 30, "time": 211.5},
    ("Qwen3-30B-A3B-MegaScience-8bit-mlx", "TRUTHFULQA"):     {"acc": 93.3, "correct": 28, "total": 30, "time": 187.9},
    ("Qwen3-30B-A3B-MegaScience-8bit-mlx", "ARC_CHALLENGE"):  {"acc": 86.7, "correct": 26, "total": 30, "time": 165.3},
    ("Qwen3-30B-A3B-MegaScience-8bit-mlx", "WINOGRANDE"):     {"acc": 73.3, "correct": 22, "total": 30, "time": 44.0},
    ("Qwen3-30B-A3B-MegaScience-8bit-mlx", "MATHQA"):         {"acc": 90.0, "correct": 27, "total": 30, "time": 704.3},
    ("Qwen3-30B-A3B-MegaScience-8bit-mlx", "BBQ"):            {"acc": 90.0, "correct": 27, "total": 30, "time": 118.6},
    ("Qwen3-30B-A3B-MegaScience-8bit-mlx", "SAFETYBENCH"):    {"acc": 83.3, "correct": 25, "total": 30, "time": 160.3},
    # Huihui-Qwen3.6-35B-A3B
    ("Huihui-Qwen3.6-35B-A3B-6bit-mlx", "MMLU_PRO"):          {"acc": 70.0, "correct": 21, "total": 30, "time": 1867.6},
    ("Huihui-Qwen3.6-35B-A3B-6bit-mlx", "HELLASWAG"):         {"acc": 90.0, "correct": 27, "total": 30, "time": 561.3},
    ("Huihui-Qwen3.6-35B-A3B-6bit-mlx", "TRUTHFULQA"):        {"acc": 83.3, "correct": 25, "total": 30, "time": 575.1},
    ("Huihui-Qwen3.6-35B-A3B-6bit-mlx", "ARC_CHALLENGE"):     {"acc": 93.3, "correct": 28, "total": 30, "time": 709.8},
    ("Huihui-Qwen3.6-35B-A3B-6bit-mlx", "WINOGRANDE"):        {"acc": 90.0, "correct": 27, "total": 30, "time": 545.7},
    ("Huihui-Qwen3.6-35B-A3B-6bit-mlx", "MATHQA"):            {"acc": 90.0, "correct": 27, "total": 30, "time": 1413.9},
    ("Huihui-Qwen3.6-35B-A3B-6bit-mlx", "BBQ"):               {"acc": 90.0, "correct": 27, "total": 30, "time": 401.3},
    ("Huihui-Qwen3.6-35B-A3B-6bit-mlx", "SAFETYBENCH"):       {"acc": 86.7, "correct": 26, "total": 30, "time": 550.5},
    # Qwen3.5-35B-A3B
    ("Qwen3.5-35B-A3B-6bit-mlx", "MMLU_PRO"):       {"acc": 76.7, "correct": 23, "total": 30, "time": 1693.6},
    ("Qwen3.5-35B-A3B-6bit-mlx", "HELLASWAG"):      {"acc": 90.0, "correct": 27, "total": 30, "time": 718.4},
    ("Qwen3.5-35B-A3B-6bit-mlx", "TRUTHFULQA"):     {"acc": 100.0, "correct": 30, "total": 30, "time": 742.0},
    ("Qwen3.5-35B-A3B-6bit-mlx", "ARC_CHALLENGE"):  {"acc": 90.0, "correct": 27, "total": 30, "time": 456.5},
    ("Qwen3.5-35B-A3B-6bit-mlx", "WINOGRANDE"):     {"acc": 96.7, "correct": 29, "total": 30, "time": 925.0},
    ("Qwen3.5-35B-A3B-6bit-mlx", "MATHQA"):         {"acc": 93.3, "correct": 28, "total": 30, "time": 1139.2},
    ("Qwen3.5-35B-A3B-6bit-mlx", "BBQ"):            {"acc": 93.3, "correct": 28, "total": 30, "time": 766.5},
    ("Qwen3.5-35B-A3B-6bit-mlx", "SAFETYBENCH"):    {"acc": 86.7, "correct": 26, "total": 30, "time": 893.5},
    # Qwen3.6-35B-A3B
    ("Qwen3.6-35B-A3B-MLX-oQ6", "MMLU_PRO"):       {"acc": 66.7, "correct": 20, "total": 30, "time": 1412.0},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "ARC_CHALLENGE"):  {"acc": 90.0, "correct": 27, "total": 30, "time": 389.8},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "MATHQA"):         {"acc": 90.0, "correct": 27, "total": 30, "time": 1100.0},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "HELLASWAG"):      {"acc": 86.7, "correct": 26, "total": 30, "time": 477.9},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "BBQ"):            {"acc": 93.3, "correct": 28, "total": 30, "time": 292.4},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "TRUTHFULQA"):     {"acc": 96.7, "correct": 29, "total": 30, "time": 442.9},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "WINOGRANDE"):     {"acc": 86.7, "correct": 26, "total": 30, "time": 472.4},
    ("Qwen3.6-35B-A3B-MLX-oQ6", "SAFETYBENCH"):    {"acc": 86.7, "correct": 26, "total": 30, "time": 357.9},
    # GLM-4.7-Flash
    ("GLM-4.7-Flash-6bit-mlx", "MMLU_PRO"):       {"acc": 70.0, "correct": 21, "total": 30, "time": 1952.1},
    ("GLM-4.7-Flash-6bit-mlx", "ARC_CHALLENGE"):   {"acc": 80.0, "correct": 24, "total": 30, "time": 334.4},
    ("GLM-4.7-Flash-6bit-mlx", "MATHQA"):          {"acc": 90.0, "correct": 27, "total": 30, "time": 1366.6},
    ("GLM-4.7-Flash-6bit-mlx", "HELLASWAG"):       {"acc": 73.3, "correct": 22, "total": 30, "time": 1289.7},
    ("GLM-4.7-Flash-6bit-mlx", "BBQ"):             {"acc": 90.0, "correct": 27, "total": 30, "time": 519.0},
    ("GLM-4.7-Flash-6bit-mlx", "TRUTHFULQA"):      {"acc": 76.7, "correct": 23, "total": 30, "time": 1223.8},
    ("GLM-4.7-Flash-6bit-mlx", "WINOGRANDE"):      {"acc": 90.0, "correct": 27, "total": 30, "time": 499.2},
    ("GLM-4.7-Flash-6bit-mlx", "SAFETYBENCH"):     {"acc": 96.7, "correct": 29, "total": 30, "time": 353.7},
    # gemma-4-26B-oQ6
    ("gemma-4-26B-A4B-it-oQ6", "MMLU_PRO"):       {"acc": 60.0, "correct": 18, "total": 30, "time": 2940.6},
    ("gemma-4-26B-A4B-it-oQ6", "ARC_CHALLENGE"):  {"acc": 90.0, "correct": 27, "total": 30, "time": 565.7},
    ("gemma-4-26B-A4B-it-oQ6", "MATHQA"):         {"acc": 76.7, "correct": 23, "total": 30, "time": 2105.3},
    ("gemma-4-26B-A4B-it-oQ6", "HELLASWAG"):      {"acc": 90.0, "correct": 27, "total": 30, "time": 991.2},
    ("gemma-4-26B-A4B-it-oQ6", "BBQ"):            {"acc": 90.0, "correct": 27, "total": 30, "time": 232.5},
    ("gemma-4-26B-A4B-it-oQ6", "TRUTHFULQA"):     {"acc": 76.7, "correct": 23, "total": 30, "time": 1534.8},
    ("gemma-4-26B-A4B-it-oQ6", "WINOGRANDE"):     {"acc": 96.7, "correct": 29, "total": 30, "time": 492.7},
    ("gemma-4-26B-A4B-it-oQ6", "SAFETYBENCH"):    {"acc": 93.3, "correct": 28, "total": 30, "time": 445.2},
    # gpt-oss-20b
    ("gpt-oss-20b-MXFP4-Q8", "MMLU_PRO"):          {"acc": 80.0, "correct": 24, "total": 30, "time": 237.0},
    ("gpt-oss-20b-MXFP4-Q8", "ARC_CHALLENGE"):     {"acc": 86.7, "correct": 26, "total": 30, "time": 72.0},
    ("gpt-oss-20b-MXFP4-Q8", "MATHQA"):            {"acc": 93.3, "correct": 28, "total": 30, "time": 413.4},
    ("gpt-oss-20b-MXFP4-Q8", "HELLASWAG"):         {"acc": 76.7, "correct": 23, "total": 30, "time": 201.9},
    ("gpt-oss-20b-MXFP4-Q8", "BBQ"):               {"acc": 93.3, "correct": 28, "total": 30, "time": 148.9},
    ("gpt-oss-20b-MXFP4-Q8", "TRUTHFULQA"):        {"acc": 86.7, "correct": 26, "total": 30, "time": 117.4},
    ("gpt-oss-20b-MXFP4-Q8", "WINOGRANDE"):        {"acc": 70.0, "correct": 21, "total": 30, "time": 139.6},
    ("gpt-oss-20b-MXFP4-Q8", "SAFETYBENCH"):       {"acc": 96.7, "correct": 29, "total": 30, "time": 102.8},
    # Qwen3.5-2B
    ("Qwen3.5-2B-MLX-8bit", "MMLU_PRO"):            {"acc": 33.3, "correct": 10, "total": 30, "time": 1999.6},
    ("Qwen3.5-2B-MLX-8bit", "ARC_CHALLENGE"):       {"acc": 76.7, "correct": 23, "total": 30, "time": 745.0},
    ("Qwen3.5-2B-MLX-8bit", "MATHQA"):              {"acc": 66.7, "correct": 20, "total": 30, "time": 1520.2},
    ("Qwen3.5-2B-MLX-8bit", "HELLASWAG"):           {"acc": 43.3, "correct": 13, "total": 30, "time": 1560.3},
    ("Qwen3.5-2B-MLX-8bit", "BBQ"):                 {"acc": 83.3, "correct": 25, "total": 30, "time": 780.1},
    ("Qwen3.5-2B-MLX-8bit", "TRUTHFULQA"):          {"acc": 36.7, "correct": 11, "total": 30, "time": 1883.1},
    ("Qwen3.5-2B-MLX-8bit", "WINOGRANDE"):          {"acc": 66.7, "correct": 20, "total": 30, "time": 1673.1},
    ("Qwen3.5-2B-MLX-8bit", "SAFETYBENCH"):         {"acc": 83.3, "correct": 25, "total": 30, "time": 1197.0},
    # Assistant_Pepe_8B
    ("Assistant_Pepe_8B-8bit-mlx", "MMLU_PRO"):     {"acc": 40.0, "correct": 12, "total": 30, "time": 19.1},
    ("Assistant_Pepe_8B-8bit-mlx", "HELLASWAG"):    {"acc": 66.7, "correct": 20, "total": 30, "time": 17.9},
    ("Assistant_Pepe_8B-8bit-mlx", "TRUTHFULQA"):   {"acc": 46.7, "correct": 14, "total": 30, "time": 16.9},
    ("Assistant_Pepe_8B-8bit-mlx", "ARC_CHALLENGE"):{"acc": 70.0, "correct": 21, "total": 30, "time": 15.4},
    ("Assistant_Pepe_8B-8bit-mlx", "WINOGRANDE"):   {"acc": 63.3, "correct": 19, "total": 30, "time": 15.2},
    ("Assistant_Pepe_8B-8bit-mlx", "MATHQA"):       {"acc": 43.3, "correct": 13, "total": 30, "time": 18.4},
    ("Assistant_Pepe_8B-8bit-mlx", "BBQ"):          {"acc": 56.7, "correct": 17, "total": 30, "time": 20.0},
    ("Assistant_Pepe_8B-8bit-mlx", "SAFETYBENCH"):  {"acc": 93.3, "correct": 28, "total": 30, "time": 19.5},
    # Llama-3.3-8B-Abliterated
    ("Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx", "MMLU_PRO"):      {"acc": 36.7, "correct": 11, "total": 30, "time": 62.3},
    ("Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx", "HELLASWAG"):     {"acc": 76.7, "correct": 23, "total": 30, "time": 15.8},
    ("Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx", "TRUTHFULQA"):    {"acc": 70.0, "correct": 21, "total": 30, "time": 18.2},
    ("Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx", "ARC_CHALLENGE"): {"acc": 66.7, "correct": 20, "total": 30, "time": 16.5},
    ("Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx", "WINOGRANDE"):    {"acc": 63.3, "correct": 19, "total": 30, "time": 13.8},
    ("Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx", "MATHQA"):        {"acc": 43.3, "correct": 13, "total": 30, "time": 40.7},
    ("Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx", "BBQ"):           {"acc": 73.3, "correct": 22, "total": 30, "time": 17.9},
    ("Llama-3.3-8B-Instruct-128K_Abliterated-8bit-mlx", "SAFETYBENCH"):   {"acc": 90.0, "correct": 27, "total": 30, "time": 19.1},
    # Hypnos-i1-8B
    ("Hypnos-i1-8B-8bit-mlx", "MMLU_PRO"):      {"acc": 30.0, "correct": 9, "total": 30, "time": 25.8},
    ("Hypnos-i1-8B-8bit-mlx", "HELLASWAG"):     {"acc": 73.3, "correct": 22, "total": 30, "time": 24.2},
    ("Hypnos-i1-8B-8bit-mlx", "TRUTHFULQA"):    {"acc": 56.7, "correct": 17, "total": 30, "time": 18.7},
    ("Hypnos-i1-8B-8bit-mlx", "ARC_CHALLENGE"): {"acc": 63.3, "correct": 19, "total": 30, "time": 14.6},
    ("Hypnos-i1-8B-8bit-mlx", "WINOGRANDE"):    {"acc": 40.0, "correct": 12, "total": 30, "time": 13.6},
    ("Hypnos-i1-8B-8bit-mlx", "MATHQA"):        {"acc": 30.0, "correct": 9, "total": 30, "time": 16.3},
    ("Hypnos-i1-8B-8bit-mlx", "BBQ"):           {"acc": 60.0, "correct": 18, "total": 30, "time": 16.6},
    ("Hypnos-i1-8B-8bit-mlx", "SAFETYBENCH"):   {"acc": 83.3, "correct": 25, "total": 30, "time": 19.7},
    # gemma-4-E4B-it
    ("gemma-4-E4B-it-MLX-8bit", "MMLU_PRO"):       {"acc": 76.7, "correct": 23, "total": 30, "time": 834.2},
    ("gemma-4-E4B-it-MLX-8bit", "HELLASWAG"):      {"acc": 70.0, "correct": 21, "total": 30, "time": 412.7},
    ("gemma-4-E4B-it-MLX-8bit", "TRUTHFULQA"):     {"acc": 66.7, "correct": 20, "total": 30, "time": 316.1},
    ("gemma-4-E4B-it-MLX-8bit", "ARC_CHALLENGE"):  {"acc": 86.7, "correct": 26, "total": 30, "time": 235.6},
    ("gemma-4-E4B-it-MLX-8bit", "WINOGRANDE"):     {"acc": 83.3, "correct": 25, "total": 30, "time": 233.1},
    ("gemma-4-E4B-it-MLX-8bit", "MATHQA"):         {"acc": 93.3, "correct": 28, "total": 30, "time": 840.1},
    ("gemma-4-E4B-it-MLX-8bit", "BBQ"):            {"acc": 93.3, "correct": 28, "total": 30, "time": 213.4},
    ("gemma-4-E4B-it-MLX-8bit", "SAFETYBENCH"):    {"acc": 83.3, "correct": 25, "total": 30, "time": 307.3},
    # Qwen3-Coder-30B
    ("Qwen3-Coder-30B-A3B-Instruct-MLX-6bit", "MMLU_PRO"):       {"acc": 46.7, "correct": 14, "total": 30, "time": 41.0},
    ("Qwen3-Coder-30B-A3B-Instruct-MLX-6bit", "HELLASWAG"):      {"acc": 73.3, "correct": 22, "total": 30, "time": 22.5},
    ("Qwen3-Coder-30B-A3B-Instruct-MLX-6bit", "TRUTHFULQA"):     {"acc": 70.0, "correct": 21, "total": 30, "time": 14.1},
    ("Qwen3-Coder-30B-A3B-Instruct-MLX-6bit", "ARC_CHALLENGE"):  {"acc": 86.7, "correct": 26, "total": 30, "time": 13.3},
    ("Qwen3-Coder-30B-A3B-Instruct-MLX-6bit", "WINOGRANDE"):     {"acc": 83.3, "correct": 25, "total": 30, "time": 14.4},
    ("Qwen3-Coder-30B-A3B-Instruct-MLX-6bit", "MATHQA"):         {"acc": 60.0, "correct": 18, "total": 30, "time": 17.7},
    ("Qwen3-Coder-30B-A3B-Instruct-MLX-6bit", "BBQ"):            {"acc": 86.7, "correct": 26, "total": 30, "time": 16.5},
    ("Qwen3-Coder-30B-A3B-Instruct-MLX-6bit", "SAFETYBENCH"):    {"acc": 80.0, "correct": 24, "total": 30, "time": 14.4},
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
        # Convert numeric expected to letter for HellaSwag (0=A) and WinoGrande (1=A)
        if expected.isdigit():
            ev = int(expected)
            # WinoGrande uses 1-indexed; HellaSwag uses 0-indexed
            expected = chr(ord('A') + (ev - 1 if ev > 0 else ev))
        if predicted.isdigit() and len(predicted) == 1:
            pv = int(predicted)
            predicted = chr(ord('A') + (pv - 1 if pv > 0 else pv))
        time_m = re.search(r"^Time: ([\d.]+)s$", body, re.M)
        q_time = float(time_m.group(1)) if time_m else 0.0

        # Extract question text:
        # Format varies by benchmark:
        #   BBQ/HellaSwag: Context: ... then Question: ... then options
        #   TruthfulQA/SafetyBench: Question: (instruction) then Question: (actual) then options
        #   WinoGrande: Question: (instruction) then Sentence: ... then numeric options
        #   MMLU/ARC/MathQA: Question: (instruction) then Question: (actual) then options
        #
        # Strategy: capture everything between the FIRST "Question:" (or "Context:"/Sentence:")
        # and the first option line (lettered A-J or numbered for WinoGrande-only cases).
        question_text = ""
        # Find the position of the first "Question:" line (the instruction line)
        q_positions = [m.start() for m in re.finditer(r"^Question:\s*", body, re.M)]
        # Also find "Context:" and "Sentence:" positions — they may precede the actual question
        ctx_positions = [m.start() for m in re.finditer(r"^Context:\s*", body, re.M)]
        sent_positions = [m.start() for m in re.finditer(r"^Sentence:\s*", body, re.M)]
        
        # The content starts at whichever comes first: Context, Sentence, or first Question
        all_starts = []
        for p in q_positions:
            all_starts.append(('q', p))
        for p in ctx_positions:
            all_starts.append(('c', p))
        for p in sent_positions:
            all_starts.append(('s', p))
        all_starts.sort(key=lambda x: x[1])
        
        if all_starts:
            # Start from the earliest relevant line
            start_pos = all_starts[0][1]
            rest = body[start_pos:]
            
            # Split into lines and accumulate until we hit options
            lines = rest.split('\n')
            q_lines = []
            for line in lines:
                # Stop at lettered option lines (A.-J.) that start the answer block
                if re.match(r'^[A-J]\.\s+\S', line) and q_lines:
                    break
                # Stop at "Answer:" line
                if re.match(r'^Answer:\s*$', line):
                    break
                q_lines.append(line)
            
            # Now strip the instruction line(s) — keep only from the LAST
            # "Question:"/"Context:"/"Sentence:" onwards, but re-include
            # Context/Sentence if they precede the actual question.
            full_text = '\n'.join(q_lines)
            
            # Find the last Question:/Context:/Sentence: position within our captured text
            # We want to keep Context/Sentence if they come BEFORE the last Question:
            last_q = None
            last_ctx = None
            last_sent = None
            for m in re.finditer(r'^Question:\s*', full_text, re.M):
                last_q = m.start()
            for m in re.finditer(r'^Context:\s*', full_text, re.M):
                last_ctx = m.start()
            for m in re.finditer(r'^Sentence:\s*', full_text, re.M):
                last_sent = m.start()
            
            # If there's a Context: or Sentence: BEFORE the last Question:, include it
            content_start = last_q if last_q is not None else 0
            if last_ctx is not None and last_ctx < content_start:
                content_start = last_ctx
            if last_sent is not None and last_sent < content_start:
                content_start = last_sent
            
            if content_start > 0:
                question_text = full_text[content_start:].strip()
            else:
                question_text = full_text.strip()
            
            # Strip the "Question:" prefix from the actual question line
            question_text = re.sub(r'^Question:\s*', '', question_text, count=1)
        
        if not question_text:
            q_m2 = re.search(r"Question:\s*\n(.*?)(?=\nAnswer:)", body, re.DOTALL)
            question_text = q_m2.group(1).strip() if q_m2 else ""
        
        # If no lettered options, strip trailing numbered option lines from question text
        has_lettered = bool(re.findall(r'^[A-J]\.\s+(.+)$', body, re.M))
        if not has_lettered:
            question_text = re.sub(r'\n\d+\.\s+.*$', '', question_text, flags=re.M).strip()
        # Strip any trailing Answer:/Expected:/Time: lines that leaked in
        question_text = re.sub(r'\n(?:Answer:|Expected:|Predicted:|Raw response:).*$', '', question_text, flags=re.M|re.DOTALL).strip()

        options = re.findall(r"^([A-J])\.\s+(.+)$", body, re.M)
        # WinoGrande uses "1." / "2." instead of "A." / "B."
        if not options:
            num_opts = re.findall(r"^(\d+)\.\s+(.+)$", body, re.M)
            if num_opts:
                options = [(chr(ord('A') + int(n) - 1), t) for n, t in num_opts]
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
    st.title("Benchmark-yourself: LLM Benchmark Quiz")
    st.markdown("Test yourself against open-source models that can run in laptops, smartphones or even potatoes (for free) on real benchmark questions.")
    st.markdown("---")

    # Benchmark selection cards
    st.subheader("Choose a Benchmark")
    st.markdown("Select which benchmark you want to test yourself on:")

    for bkey in BENCHMARKS_MC:
        with st.container():
            col_sel, col_info = st.columns([1, 6])
            with col_sel:
                selected = st.button("Start", key=f"sel_{bkey}", use_container_width=True, type="primary")
            with col_info:
                num_q = len(bank.get(bkey, []))
                st.markdown(f"**{BENCH_SHORT[bkey]}** — {num_q} questions")
                st.caption(BENCH_DESC[bkey])
            if selected:
                st.session_state.benchmark = bkey
                st.session_state.page = "quiz"
                st.session_state.current_q = 0
                st.session_state.answers = {}
                st.session_state.start_time = time.time()
                st.session_state.q_start_time = time.time()
                st.session_state.q_times = []
                st.rerun()
                return
            st.markdown("---")

    # Dropdown as alternative selector — launches quiz on change
    def on_dropdown_change():
        bkey = st.session_state.dropdown_bench
        st.session_state.benchmark = bkey
        st.session_state.page = "quiz"
        st.session_state.current_q = 0
        st.session_state.answers = {}
        st.session_state.start_time = time.time()
        st.session_state.q_start_time = time.time()
        st.session_state.q_times = []

    st.selectbox("Or pick from dropdown:", BENCHMARKS_MC,
                 format_func=lambda b: f"{BENCH_SHORT[b]}  ({len(bank.get(b, []))} questions)",
                 index=0,
                 key="dropdown_bench",
                 on_change=on_dropdown_change)


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
    col_quit, col_next = st.columns([1, 1])

    with col_quit:
        if st.button("I quit, choose another quiz", use_container_width=True):
            st.session_state.page = "setup"
            st.rerun()

    with col_next:
        if choice is not None:
            selected_letter = choice[0]
            if st.button("Next  >>", type="primary", use_container_width=True):
                q_elapsed = time.time() - st.session_state.q_start_time
                st.session_state.answers[q_idx] = selected_letter
                st.session_state.q_times.append(q_elapsed)
                st.session_state.current_q = q_idx + 1
                st.session_state.q_start_time = time.time()
                st.rerun()
        else:
            st.info("Select an answer to continue.")

    # Live leaderboard: cumulative accuracy after questions answered so far
    n_answered = len(st.session_state.answers)
    if n_answered > 0:
        st.markdown("---")
        _draw_live_leaderboard(bank, bench, questions, n_answered)

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


def _draw_live_leaderboard(bank, bench, questions, n_answered):
    """Draw a horizontal bar chart of cumulative accuracy (sorted high→low)
    comparing the user against all AI models on the questions answered so far."""
    answers = st.session_state.answers
    answered_indices = sorted(answers.keys())[:n_answered]

    # User accuracy on answered questions
    user_correct = sum(
        1 for i in answered_indices
        if i < len(questions) and answers[i] == questions[i]["expected"]
    )
    user_acc = user_correct / len(answered_indices) * 100 if answered_indices else 0.0

    # AI accuracy on the same questions
    rows = [("You", user_acc, "#FFD700")]  # gold for user
    for model in MODELS:
        if (model, bench) not in SUMMARY:
            continue
        ai_correct = 0
        for i in answered_indices:
            if i < len(questions):
                q = questions[i]
                m_short = SHORT[model]
                if q["model_correct"].get(m_short, False):
                    ai_correct += 1
        ai_acc = ai_correct / len(answered_indices) * 100 if answered_indices else 0.0
        rows.append((SHORT[model], ai_acc, COLORS[model]))

    # Sort by accuracy descending; ties broken by name
    rows.sort(key=lambda r: (-r[1], r[0]))

    names = [r[0] for r in rows]
    accs = [r[1] for r in rows]
    colors = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(8, max(3, len(rows) * 0.45)))
    y_pos = range(len(names))
    bars = ax.barh(y_pos, accs, color=colors, edgecolor="black", linewidth=0.5, height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10)
    ax.invert_yaxis()  # highest at top
    ax.set_xlim(0, 105)
    ax.set_xlabel("Accuracy (%)", fontsize=10)
    ax.set_title(f"Live Leaderboard  ({len(answered_indices)} questions answered)", fontsize=12, fontweight="bold")

    # Value labels
    for bar, acc in zip(bars, accs):
        ax.text(min(acc + 1.5, 88), bar.get_y() + bar.get_height() / 2,
                f"{acc:.1f}%", va="center", fontsize=9, fontweight="bold")

    ax.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def page_results(bank):
    bench = st.session_state.benchmark
    questions = bank[bench]
    answers = st.session_state.answers
    total = len(questions)

    total_time = time.time() - st.session_state.start_time
    user_correct = sum(
        1 for i, q in enumerate(questions) if i in answers and answers[i] == q["expected"]
    )
    user_acc = user_correct / total * 100 if total > 0 else 0.0

    st.title("Results")
    st.balloons()

    # Big metrics
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Your Accuracy", f"{user_acc:.1f}%", f"{user_correct}/{total} correct")
    col_m2.metric("Your Time", f"{total_time:.1f}s")
    col_m3.metric("Your Avg/q", f"{total_time/max(total,1):.1f}s")

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

    n_q = min(len(st.session_state.q_times), len(questions))
    q_indices = list(range(n_q))
    user_q_times = st.session_state.q_times[:n_q]
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
