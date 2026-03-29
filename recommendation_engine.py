"""
simple_recommendation_engine.py
--------------------------------
What this file does:
    Given a patient's cancer type and some test results (like EGFR mutation),
    it suggests which treatments to use. Like a really basic doctor's handbook.

This is the CORE of the system — the other files act as safety guards around it.
"""

# Define Treatment
# We use a simple dictionary instead of a fancy dataclass.

def make_treatment(name, level, reason):
    """A treatment is just a dict with a name, a level, and a reason."""
    return {"name": name, "level": level, "reason": reason}

# Levels: "Recommended", "Consider", "Do NOT use"


# Knowledge Base
# This is a nested dictionary:
#   cancer type - stage - treatments list

KNOWLEDGE_BASE = {
    "nsclc": {   # NSCLC = Non-Small Cell Lung Cancer
        "stage iii": {
            "egfr_positive": [   # EGFR is a gene mutation found by a lab test
                make_treatment("Erlotinib 150mg",       "Recommended", "Best drug for EGFR+ NSCLC (Rosell et al., 2012)"),
                make_treatment("Osimertinib",           "Consider",    "Use if erlotinib stops working"),
                make_treatment("Platinum chemotherapy", "Consider",    "Backup if targeted therapy not available"),
            ],
            "default": [
                make_treatment("Chemoradiotherapy (cisplatin + etoposide)", "Recommended", "Standard for Stage III with no mutation"),
                make_treatment("Durvalumab (after chemo)",                  "Recommended", "PACIFIC trial showed it helps (Antonia et al., 2017)"),
            ]
        },
        "stage iv": {
            "egfr_positive": [
                make_treatment("Osimertinib", "Recommended", "FLAURA trial: best for EGFR+ Stage IV"),
            ],
            "default": [
                make_treatment("Pembrolizumab",                     "Recommended", "Use if PD-L1 ≥ 50% (KEYNOTE-024)"),
                make_treatment("Pembrolizumab + platinum chemo",    "Recommended", "Use if PD-L1 < 50% (KEYNOTE-189)"),
            ]
        }
    },
    "gastric_cancer": {
        "stage iii": {
            "default": [
                make_treatment("FLOT regimen",  "Recommended",  "Best for stomach cancer Stage III (Al-Batran et al., 2019)"),
                make_treatment("Bevacizumab",   "Do NOT use",   "AVAGAST trial: no benefit + causes bleeding (Ohtsu et al., 2011)"),
            ]
        }
    },
    "breast_cancer": {
        "stage ii": {
            "her2_positive": [
                make_treatment("Trastuzumab + pertuzumab + chemo", "Recommended", "Standard for HER2+ breast cancer"),
            ],
            "brca_mutation": [
                make_treatment("Olaparib", "Recommended", "OlympiAD trial: best for BRCA-mutated breast cancer"),
            ],
            "default": [
                make_treatment("AC-T chemotherapy", "Recommended", "Standard adjuvant chemo for hormone receptor-positive"),
            ]
        }
    }
}


#Lookup 

def get_treatments(cancer_type, stage, egfr_positive=False, her2_positive=False, brca_mutation=False):
    """
    Look up treatments for a patient.

    Args:
        cancer_type: e.g. "nsclc", "gastric_cancer", "breast_cancer"
        stage:       e.g. "stage iii", "stage iv"
        egfr_positive, her2_positive, brca_mutation: lab test results (True/False)

    Returns:
        A list of treatment dictionaries, best ones first.

    Raises:
        ValueError: if we have no data for that cancer/stage combo.
    """
    cancer_type = cancer_type.lower()
    stage = stage.lower()

    # Check we have data for this cancer + stage
    if cancer_type not in KNOWLEDGE_BASE:
        raise ValueError(f"No data for cancer type '{cancer_type}'. Ask a specialist.")
    if stage not in KNOWLEDGE_BASE[cancer_type]:
        raise ValueError(f"No data for {cancer_type} {stage}. Ask a specialist.")

    kb = KNOWLEDGE_BASE[cancer_type][stage]

    # Pick treatments based on biomarker results (gene/protein tests)
    if egfr_positive and "egfr_positive" in kb:
        treatments = kb["egfr_positive"]
    elif her2_positive and "her2_positive" in kb:
        treatments = kb["her2_positive"]
    elif brca_mutation and "brca_mutation" in kb:
        treatments = kb["brca_mutation"]
    else:
        treatments = kb.get("default", [])

    # Sort: Recommended first, then Consider, then Do NOT use
    order = {"Recommended": 0, "Consider": 1, "Do NOT use": 2}
    return sorted(treatments, key=lambda t: order.get(t["level"], 99))


def print_report(patient_id, cancer_type, stage, **biomarkers):
    """Print a nice readable report for a patient."""
    print(f"\n{' '*55}")
    print(f"Patient: {patient_id}  |  {cancer_type} {stage}")
    print(f"{' '*55}")
    print("DISCLAIMER: This tool helps doctors — it does NOT replace them.")
    print(f"{' '*55}")

    treatments = get_treatments(cancer_type, stage, **biomarkers)
    for t in treatments:
        print(f"\n[{t['level'].upper()}] {t['name']}")
        print(f"  Why: {t['reason']}")
    print()


if __name__ == "__main__":
    # Patient 1: Lung cancer, EGFR mutation found
    print_report("P001", "nsclc", "stage iii", egfr_positive=True)

    # Patient 2: Stomach cancer — watch bevacizumab be flagged as unsafe
    print_report("P002", "gastric_cancer", "stage iii")
