"""
using Z3 to formally PROVE whether a combination of patient + drug is allowed or blocked.
"""

from z3 import Bool, Solver, And, Not, Implies, BoolVal, sat


# Facts

# Patient facts
patient_has_gastric_cancer   = Bool("patient_has_gastric_cancer")
patient_has_nsclc            = Bool("patient_has_nsclc")
patient_has_bleeding_risk    = Bool("patient_has_bleeding_risk")
patient_has_egfr_mutation    = Bool("patient_has_egfr_mutation")

# Treatment choices (only one drug at a time in these tests)
giving_bevacizumab           = Bool("giving_bevacizumab")
giving_erlotinib             = Bool("giving_erlotinib")
giving_flot_regimen          = Bool("giving_flot_regimen")

# The outcome we want Z3 to check
recommendation_is_safe       = Bool("recommendation_is_safe")


# Safety Rules
# Implies(A, B) means: "If A is true, then B must be true."

SAFETY_RULES = [

    # Rule 1: Bevacizumab + gastric cancer = UNSAFE
    # Why: AVAGAST trial (Ohtsu et al., 2011) showed no benefit + bleeding risk.
    #      This is one of the real failures of Watson for Oncology (Ross & Swetlitz, 2017).
    Implies(
        And(patient_has_gastric_cancer, giving_bevacizumab),
        Not(recommendation_is_safe)    # → it is NOT safe
    ),

    # Rule 2: Bevacizumab + any patient with bleeding risk = UNSAFE
    # Why: Bevacizumab stops blood clotting. Very dangerous if bleeding already.
    Implies(
        And(giving_bevacizumab, patient_has_bleeding_risk),
        Not(recommendation_is_safe)
    ),

    # Rule 3: Erlotinib + NSCLC + EGFR mutation = SAFE ✓
    # Why: Strong clinical trial evidence (Rosell et al., 2012, NEJM).
    Implies(
        And(patient_has_nsclc, patient_has_egfr_mutation, giving_erlotinib),
        recommendation_is_safe
    ),

    # Rule 4: FLOT regimen + gastric cancer = SAFE ✓
    # Why: Al-Batran et al. (2019), Lancet — this is the standard of care.
    Implies(
        And(patient_has_gastric_cancer, giving_flot_regimen),
        recommendation_is_safe
    ),
]


# Checker

def is_safe(scenario: dict, label: str = "") -> bool:
    """
    Check if a treatment is safe for a patient.

    Args:
        scenario: a dict of {Z3 variable: True or False}
                  describing the patient and what drug we're giving.
        label:    optional name for this test (just for printing)

    Returns:
        True if safe, False if blocked.
    """
    if label:
        print(f"\n--- {label} ---")

    solver = Solver()

    # Add the medical rules
    for rule in SAFETY_RULES:
        solver.add(rule)

    # Add the facts about this specific patient + drug
    for variable, value in scenario.items():
        solver.add(variable == BoolVal(value))

    # Ask Z3: is it possible for "recommendation_is_safe" to be True?
    solver.add(recommendation_is_safe == BoolVal(True))
    result = solver.check()

    safe = (result == sat)

    if safe:
        print("  Z3 says: SAFE — recommendation is allowed.")
    else:
        print("  Z3 says: UNSAFE — recommendation is BLOCKED.")
        # Show which rule was broken
        if scenario.get(patient_has_gastric_cancer) and scenario.get(giving_bevacizumab):
            print("  Reason: Bevacizumab is dangerous in gastric cancer.")
            print("          (AVAGAST trial failure + WfO documented error)")
        if scenario.get(giving_bevacizumab) and scenario.get(patient_has_bleeding_risk):
            print("  Reason: Patient has bleeding risk — bevacizumab is contraindicated.")
        print("  ACTION: Escalate to a senior oncologist before proceeding.")

    return safe


# Formal Proof

def prove_bevacizumab_never_safe_in_gastric_cancer():
    """
    This proves: "Is there ANY possible patient where bevacizumab is safe
    in gastric cancer?" — not just one test case, but ALL possible cases.

    If Z3 says UNSAT, it's MATHEMATICALLY IMPOSSIBLE. A proof, not a test.
    """
    print("\n" + " "*55)
    print("PROOF: Can bevacizumab EVER be safe in gastric cancer?")
    print(" "*55)

    solver = Solver()
    for rule in SAFETY_RULES:
        solver.add(rule)

    # Fix these two facts as always-true
    solver.add(patient_has_gastric_cancer == BoolVal(True))
    solver.add(giving_bevacizumab         == BoolVal(True))

    # Ask: can it ever be safe?
    solver.add(recommendation_is_safe == BoolVal(True))

    result = solver.check()

    if result == sat:
        print("Unexpected: Z3 found a scenario where it could be safe. Check rules!")
    else:
        print("Z3 result: UNSAT")
        print("PROOF: There is NO possible patient where bevacizumab is safe")
        print("in gastric cancer. This is a mathematical guarantee — not just")
        print("a test of one scenario, but ALL scenarios simultaneously.")

    print(" "*55)


if __name__ == "__main__":

    # Test 1: Safe — erlotinib for a lung cancer patient with EGFR mutation
    is_safe(
        label="Erlotinib for NSCLC + EGFR mutation (should be SAFE)",
        scenario={
            patient_has_nsclc:          True,
            patient_has_egfr_mutation:  True,
            giving_erlotinib:           True,
            patient_has_gastric_cancer: False,
            patient_has_bleeding_risk:  False,
            giving_bevacizumab:         False,
            giving_flot_regimen:        False,
        }
    )

    # Test 2: Blocked — bevacizumab for gastric cancer (the real WfO failure)
    is_safe(
        label="Bevacizumab for gastric cancer (should be BLOCKED)",
        scenario={
            patient_has_gastric_cancer: True,
            giving_bevacizumab:         True,
            patient_has_nsclc:          False,
            patient_has_egfr_mutation:  False,
            patient_has_bleeding_risk:  False,
            giving_erlotinib:           False,
            giving_flot_regimen:        False,
        }
    )

    # Test 3: Blocked — bevacizumab + patient has bleeding risk
    is_safe(
        label="Bevacizumab + patient has bleeding risk (should be BLOCKED)",
        scenario={
            patient_has_nsclc:          True,
            giving_bevacizumab:         True,
            patient_has_bleeding_risk:  True,
            patient_has_gastric_cancer: False,
            patient_has_egfr_mutation:  False,
            giving_erlotinib:           False,
            giving_flot_regimen:        False,
        }
    )

    # Test 4: Safe — FLOT for gastric cancer
    is_safe(
        label="FLOT regimen for gastric cancer (should be SAFE)",
        scenario={
            patient_has_gastric_cancer: True,
            giving_flot_regimen:        True,
            giving_bevacizumab:         False,
            patient_has_nsclc:          False,
            patient_has_egfr_mutation:  False,
            patient_has_bleeding_risk:  False,
            giving_erlotinib:           False,
        }
    )

    # Bonus: a mathematical proof about the rules themselves
    prove_bevacizumab_never_safe_in_gastric_cancer()
