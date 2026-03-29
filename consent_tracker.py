"""
Check Patient Consent an dtransparency
"""

from z3 import Bool, Solver, And, Implies, BoolVal, sat


#Declare facts

ai_was_involved            = Bool("ai_was_involved")
patient_was_told           = Bool("patient_was_told")       # Did patient know AI was used?
doctor_acknowledged        = Bool("doctor_acknowledged")    # Did doctor sign off?
consent_is_written_or_digital = Bool("consent_is_written_or_digital")  # Not just verbal
this_is_high_risk          = Bool("this_is_high_risk")      # Cancer = always high risk
record_can_be_finalised    = Bool("record_can_be_finalised")  # What we want to check


#Rules

CONSENT_RULES = [

    # Rule 1: If AI was involved - patient must be told before finalising
    # Legal basis: GDPR Article 22
    Implies(
        ai_was_involved,
        Implies(record_can_be_finalised, patient_was_told)
    ),

    # Rule 2: Doctor must ALWAYS acknowledge AI involvement before finalising
    # Legal basis: EU AI Act Article 14 (human oversight)
    Implies(
        record_can_be_finalised,
        doctor_acknowledged
    ),

    # Rule 3: High-risk decisions (cancer) need written/digital consent — not verbal
    # Legal basis: EU AI Act Article 13
    Implies(
        And(this_is_high_risk, record_can_be_finalised),
        consent_is_written_or_digital
    ),

    # Rule 4: Written consent only counts if the patient was actually told
    # (you can't sign something you weren't told about)
    Implies(
        consent_is_written_or_digital,
        patient_was_told
    ),
]


#Checker

def can_finalise(scenario: dict, label: str = "") -> bool:
    if label:
        print(f"\n--- {label} ---")

    solver = Solver()
    for rule in CONSENT_RULES:
        solver.add(rule)
    for variable, value in scenario.items():
        solver.add(variable == BoolVal(value))
    solver.add(record_can_be_finalised == BoolVal(True))

    result = solver.check()
    allowed = (result == sat)

    if allowed:
        print("  Z3 says: ALLOWED — record can be finalised.")
    else:
        print("  Z3 says: BLOCKED — cannot finalise this record.")
        s = scenario
        if s.get(ai_was_involved) and not s.get(patient_was_told):
            print("  Reason: Patient was NOT told AI was involved. (GDPR Art. 22)")
        if not s.get(doctor_acknowledged):
            print("  Reason: Doctor has NOT acknowledged AI involvement. (EU AI Act Art. 14)")
        if s.get(this_is_high_risk) and not s.get(consent_is_written_or_digital):
            print("  Reason: Cancer decisions need written/digital consent — verbal not enough.")

    return allowed


# Formal Proof

def prove_no_consent_no_finalise():
    """
    Prove: Is there ANY way to finalise without patient consent?
    Expected: No — UNSAT — mathematically impossible.
    """
    print("\n" + " "*55)
    print("PROOF: Can we ever finalise without patient consent?")
    print(" "*55)

    solver = Solver()
    for rule in CONSENT_RULES:
        solver.add(rule)
    solver.add(ai_was_involved         == BoolVal(True))
    solver.add(record_can_be_finalised == BoolVal(True))
    solver.add(patient_was_told        == BoolVal(False))  # Patient NOT told

    result = solver.check()
    if result == sat:
        print("Z3 found a loophole! Review your rules.")
    else:
        print("Z3 result: UNSAT")
        print("PROOF: It is IMPOSSIBLE to finalise without telling the patient.")
        print("This holds for every possible combination of other conditions.")
    print(" "*55)


def prove_doctor_always_needed():
    """
    Prove: Even if the patient consents, is the doctor's sign-off still required?
    Expected: Yes — UNSAT — patient consent alone is never enough.
    """
    print("\n" + " "*55)
    print("PROOF: Is doctor sign-off required even with full patient consent?")
    print(" "*55)

    solver = Solver()
    for rule in CONSENT_RULES:
        solver.add(rule)
    solver.add(ai_was_involved         == BoolVal(True))
    solver.add(patient_was_told        == BoolVal(True))   # Patient IS told
    solver.add(record_can_be_finalised == BoolVal(True))
    solver.add(doctor_acknowledged     == BoolVal(False))  # Doctor NOT acknowledged

    result = solver.check()
    if result == sat:
        print("Z3: Doctor can be skipped. Review your rules.")
    else:
        print("Z3 result: UNSAT")
        print("PROOF: Even with full patient consent, doctor sign-off is ALWAYS needed.")
        print("Patient consent alone is not enough. (EU AI Act Art. 14)")
    print(" "*55)



class ConsentRecord:
    """
    A medical record that uses Z3 to check consent before it can be saved.
    Usage:
        rec = ConsentRecord("P001", "NSCLC", "Erlotinib")
        rec.patient_gave_consent(method="digital")
        rec.doctor_signed_off("Dr. Smith")
        rec.finalise()   # Only works if Z3 says it's allowed
    """
    def __init__(self, patient_id, cancer_type, treatment):
        self.patient_id  = patient_id
        self.cancer_type = cancer_type
        self.treatment   = treatment
        self._patient_told  = False
        self._consent_method = None
        self._doctor_acked   = False
        self._finalised      = False

    def patient_gave_consent(self, method="verbal"):
        """Record that the patient was informed. method = 'verbal', 'written', or 'digital'."""
        if method not in {"verbal", "written", "digital"}:
            raise ValueError(f"'{method}' is not a valid consent method.")
        self._patient_told  = True
        self._consent_method = method
        print(f"[{self.patient_id}] Patient consent recorded via {method}.")
        if method == "verbal":
            print(f"  Warning: verbal consent may not be enough for cancer decisions.")

    def doctor_signed_off(self, doctor_id):
        """Record that the doctor acknowledged the AI recommendation."""
        self._doctor_acked = True
        print(f"[{self.patient_id}] Doctor '{doctor_id}' has acknowledged AI involvement.")

    def finalise(self):
        """Try to finalise the record. Z3 will block it if rules aren't met."""
        valid_consent = self._consent_method in {"written", "digital"}

        allowed = can_finalise(
            label=f"Finalising record for {self.patient_id}",
            scenario={
                ai_was_involved:                True,
                patient_was_told:               self._patient_told,
                doctor_acknowledged:            self._doctor_acked,
                consent_is_written_or_digital:  valid_consent,
                this_is_high_risk:              True,  # Cancer is always high-risk
            }
        )

        if not allowed:
            raise PermissionError(
                f"[{self.patient_id}] Record cannot be finalised — consent rules not met."
            )
        self._finalised = True
        print(f"[{self.patient_id}] Record finalised successfully.")


if __name__ == "__main__":

    # Test 1: Blocked — no consent, no doctor sign-off
    can_finalise(
        label="No consent, no doctor sign-off (should be BLOCKED)",
        scenario={
            ai_was_involved:               True,
            patient_was_told:              False,
            doctor_acknowledged:           False,
            consent_is_written_or_digital: False,
            this_is_high_risk:             True,
        }
    )

    # Test 2: Blocked — patient told verbally, doctor not involved
    can_finalise(
        label="Verbal consent only, no doctor ACK (should be BLOCKED)",
        scenario={
            ai_was_involved:               True,
            patient_was_told:              True,
            doctor_acknowledged:           False,
            consent_is_written_or_digital: False,   # verbal = not valid for high-risk
            this_is_high_risk:             True,
        }
    )

    # Test 3: Allowed — digital consent + doctor signed off
    can_finalise(
        label="Digital consent + doctor ACK (should be ALLOWED)",
        scenario={
            ai_was_involved:               True,
            patient_was_told:              True,
            doctor_acknowledged:           True,
            consent_is_written_or_digital: True,
            this_is_high_risk:             True,
        }
    )

    # Formal proofs
    prove_no_consent_no_finalise()
    prove_doctor_always_needed()

    # Full record demo
    print("\n\n FULL RECORD ")
    rec = ConsentRecord("P002", "NSCLC Stage III", "Durvalumab")
    rec.patient_gave_consent(method="digital")
    rec.doctor_signed_off("Dr. Patel")
    rec.finalise()
