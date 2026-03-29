"""
check if update is trustworthy
"""

from z3 import Bool, Solver, And, Not, Implies, BoolVal, sat


#Declare facts

author_has_money_interest  = Bool("author_has_money_interest")  # Does author have financial stake?
interest_was_declared      = Bool("interest_was_declared")       # Did they disclose it?
update_was_peer_reviewed   = Bool("update_was_peer_reviewed")    # Was it checked by someone else?
reviewer_is_independent    = Bool("reviewer_is_independent")     # Not from the same company/institution
update_is_a_removal        = Bool("update_is_a_removal")         # Removing a treatment = extra risky
update_is_allowed          = Bool("update_is_allowed")           # What we want to check


#Rules

CONFLICT_OF_INTEREST_RULES = [

    # Rule 1: If there's a financial interest - it must be peer-reviewed independently
    # Basis: ICMJE (2023) conflict of interest guidelines
    Implies(
        author_has_money_interest,
        Implies(update_is_allowed, And(update_was_peer_reviewed, reviewer_is_independent))
    ),

    # Rule 2: If there's a financial interest that was NOT declared - update is BLOCKED
    # Basis: The MSKCC/Watson for Oncology failure (Ross & Swetlitz, 2017)
    Implies(
        And(author_has_money_interest, Not(interest_was_declared)),
        Not(update_is_allowed)
    ),

    # Rule 3: Removing a treatment is extra risky - always needs peer review
    # Basis: High-stakes changes need independent validation (Topol, 2019)
    Implies(
        update_is_a_removal,
        Implies(update_is_allowed, update_was_peer_reviewed)
    ),

    # Rule 4: Peer review only counts if the reviewer is truly independent
    # (A colleague from the same conflicted institution doesn't count)
    Implies(
        update_was_peer_reviewed,
        reviewer_is_independent
    ),

    # Rule 5: If no financial interest AND not a removal - update is fine without peer review
    Implies(
        And(Not(author_has_money_interest), Not(update_is_a_removal)),
        update_is_allowed
    ),
]


#Check

def is_update_allowed(scenario: dict, label: str = "") -> bool:
    """
    Check if a knowledge base update is allowed under conflict-of-interest rules.

    Args:
        scenario: dict of {Z3 variable: True or False}
        label:    optional test name for printing

    Returns:
        True if allowed, False if rejected.
    """
    if label:
        print(f"\n--- {label} ---")

    solver = Solver()
    for rule in CONFLICT_OF_INTEREST_RULES:
        solver.add(rule)
    for variable, value in scenario.items():
        solver.add(variable == BoolVal(value))
    solver.add(update_is_allowed == BoolVal(True))

    result = solver.check()
    allowed = (result == sat)

    if allowed:
        print("  Z3 says: ALLOWED — update passes conflict-of-interest checks.")
    else:
        print("  Z3 says: REJECTED — update does not pass conflict-of-interest rules.")
        s = scenario
        if s.get(author_has_money_interest) and not s.get(interest_was_declared):
            print("  Reason: Financial interest exists but was NEVER DECLARED.")
            print("          This is exactly the Watson for Oncology failure (Ross & Swetlitz, 2017).")
        if s.get(author_has_money_interest) and not s.get(update_was_peer_reviewed):
            print("  Reason: Financial interest requires independent peer review.")
        if s.get(update_is_a_removal) and not s.get(update_was_peer_reviewed):
            print("  Reason: Removing a treatment always needs peer review (high-stakes change).")
    return allowed


#Fromal Proof 

def prove_undeclared_interest_always_rejected():
    """
    Prove: If someone has an undeclared financial interest, can their update
    EVER be accepted — no matter what else is true?

    Expected: UNSAT — mathematically impossible.
    This formally captures the lesson from Watson for Oncology.
    """
    print("\n" + " "*55)
    print("PROOF: Can an undeclared financial interest ever be accepted?")
    print(" "*55)

    solver = Solver()
    for rule in CONFLICT_OF_INTEREST_RULES:
        solver.add(rule)
    solver.add(author_has_money_interest == BoolVal(True))
    solver.add(interest_was_declared     == BoolVal(False))  # NOT declared
    solver.add(update_is_allowed         == BoolVal(True))   # Can it pass?

    result = solver.check()
    if result == sat:
        print("Z3 found a way through! Review your rules.")
    else:
        print("Z3 result: UNSAT")
        print("PROOF: An undeclared financial interest ALWAYS blocks the update.")
        print("No other conditions (peer review, good intentions) can override this.")
        print("This formally encodes the lesson from Watson for Oncology.")
    print(" "*55)



if __name__ == "__main__":

    # Test 1: Clean update — no money interest, no removal
    is_update_allowed(
        label="Clean update, no conflict of interest (should be ALLOWED)",
        scenario={
            author_has_money_interest: False,
            interest_was_declared:     True,
            update_was_peer_reviewed:  False,
            reviewer_is_independent:   False,
            update_is_a_removal:       False,
        }
    )

    # Test 2: Declared interest + independent peer review
    is_update_allowed(
        label="Declared interest + independent reviewer (should be ALLOWED)",
        scenario={
            author_has_money_interest: True,
            interest_was_declared:     True,   # Declared
            update_was_peer_reviewed:  True,   # Reviewed
            reviewer_is_independent:   True,   # Independent
            update_is_a_removal:       False,
        }
    )

    # Test 3: The MSKCC/Watson scenario — interest exists but was NEVER declared
    is_update_allowed(
        label="Undeclared financial interest (the real WfO failure — should be REJECTED)",
        scenario={
            author_has_money_interest: True,
            interest_was_declared:     False,  # This is the problem
            update_was_peer_reviewed:  True,
            reviewer_is_independent:   True,
            update_is_a_removal:       False,
        }
    )

    # Test 4: Non-independent reviewer (e.g. same institution)
    is_update_allowed(
        label="Declared interest but reviewer is NOT independent (should be REJECTED)",
        scenario={
            author_has_money_interest: True,
            interest_was_declared:     True,
            update_was_peer_reviewed:  True,
            reviewer_is_independent:   False,  # Colleague, not independent
            update_is_a_removal:       False,
        }
    )

    # Formal proof
    prove_undeclared_interest_always_rejected()
