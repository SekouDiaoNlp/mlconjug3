"""
Error analysis utilities for mlconjug3 models.

This module provides diagnostic tools to evaluate model performance,
including:
- Overall accuracy computation
- Confusion pair analysis
- Inspection of misclassified verb samples

It is intended for debugging and model improvement rather than production use.
"""

import numpy as np
from collections import defaultdict, Counter


def analyze_errors(lang, y_true, y_pred, inputs, top_k=15):
    """
    Perform qualitative and quantitative error analysis on model predictions.

    This function prints:
    - Overall accuracy
    - Most frequent confusion pairs (true label → predicted label)
    - Example misclassified inputs grouped by error type

    Parameters
    ----------
    lang : str
        Language code (e.g., "fr", "en", "es").
    y_true : sequence of int or sequence of str
        Ground-truth template labels.
    y_pred : sequence of int or sequence of str
        Predicted template labels.
    inputs : sequence of str
        Input verb samples corresponding to predictions.
    top_k : int, optional
        Number of top confusion pairs to display, by default 15.

    Returns
    -------
    None
    """

    print("\n" + "=" * 30)
    print(f" ERROR ANALYSIS: {lang.upper()}")
    print("=" * 30 + "\n")

    y_true = list(y_true)
    y_pred = list(y_pred)

    acc = np.mean(np.array(y_true) == np.array(y_pred))
    print(f"Accuracy: {acc:.4f}\n")

    # -------------------------
    # CONFUSION PAIRS
    # -------------------------
    pairs = Counter()

    for t, p in zip(y_true, y_pred):
        if t != p:
            pairs[(t, p)] += 1

    print("Top confusion pairs:\n")

    for (t, p), c in pairs.most_common(top_k):
        print(f"{t} → {p} : {c}")

    # -------------------------
    # SAMPLE ERRORS
    # -------------------------
    print("\nSample misclassified verbs:\n")

    grouped = defaultdict(list)

    for x, t, p in zip(inputs, y_true, y_pred):
        if t != p:
            grouped[(t, p)].append(x)

    for (t, p), items in list(grouped.items())[:5]:
        print(f"\n{t} → {p} ({len(items)} cases)")
        print("Examples:", items[:10])
