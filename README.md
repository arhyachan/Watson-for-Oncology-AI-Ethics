# Watson-for-Oncology-AI-Ethics
# Watson for Oncology — AI Ethics Portfolio
### MSc Advanced AI | University College Dublin | February 2026

---

## Overview

This repository contains the implementation artefacts for a reflective portfolio report analysing IBM Watson for Oncology through three ethical frameworks: Utilitarianism, Kantian Deontology, and Virtue Ethics.

The code demonstrates three ethical constraints using **Z3**, a formal constraint solver developed by Microsoft Research (de Moura & Bjørner, 2008), alongside a rule-based treatment recommendation engine that mirrors the core architecture of WfO.

---

## Files

| File | Purpose |
|------|---------|
| `recommendation_engine.py` | Rule-based treatment recommendation engine (core functional component) |
| `safety_checker.py` | Z3 formal verification of clinical safety constraints (Utilitarian goal) |
| `consent_tracker.py` | Z3 formal verification of informed consent requirements (Kantian goal) |
| `conflict_of_interest.py` | Z3 formal verification of conflict-of-interest rules (Virtue Ethics goal) |

---

## How to Run

### Install the dependency

```bash
pip install z3-solver
```

### Run each module individually

```bash
python recommendation_engine.py
python safety_checker.py
python consent_tracker.py
python conflict_of_interest.py
```

Each Z3 module prints test results followed by a **formal proof** — a mathematical guarantee that certain unsafe states are impossible under all conditions, not just the cases tested.

---

## A Note on Execution Environment

The original code was developed on a local machine that is no longer available. Final execution and output verification was carried out on **Google Colab**. To replicate this:

1. Go to [colab.google.com](https://colab.google.com) and open a new notebook
2. In the first cell, run: `!pip install z3-solver`
3. Upload the `.py` files using the file panel on the left
4. In a new cell, run: `!python safety_checker.py` (repeat for each file)

Alternatively you can use the AI Ethics.ipynb file

---

## References

- de Moura, L., & Bjørner, N. (2008). Z3: An efficient SMT solver. *TACAS 2008*, LNCS vol. 4963.
- Ross, C., & Swetlitz, I. (2017). IBM pitched its Watson supercomputer as a revolution in cancer care. *STAT News*.
- Strickland, E. (2019). How IBM Watson overpromised and underdelivered on AI health care. *IEEE Spectrum*.

