"""Expanded, template-generated fictional adversarial set (360 examples).

Each template applies one perturbation with a fixed labelling rule to ten fictional
scenarios, so every label follows from the template, not from case-by-case judgment.
Labels are rule-generated and NOT independently human-verified or clinical ground truth.

Labelling conventions (consistent with the core 12 examples):
- Evidence that states a *different* detail without excluding the claimed one
  ("Module B passed" for a claim about Module A) is INSUFFICIENT.
- Evidence that explicitly excludes the claim ("Only Module B passed") is CONTRADICTED.
- Different exact counts are CONTRADICTED; exact counts are read as exhaustive.

Scenarios 1-7 form the `dev` split and scenarios 8-10 the held-out `test` split.
Tune thresholds or prompts on `dev` only; report `test` separately.
"""
from dataclasses import dataclass

from .adversarial_fixtures import AdversarialExample, SemanticLabel, _hit
from .assessment import Claim

S, C, I = SemanticLabel.SUPPORTED, SemanticLabel.CONTRADICTED, SemanticLabel.INSUFFICIENT
NUMBER_WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")

@dataclass(frozen=True)
class Scenario:
    subj: str          # lower-case mid-sentence form, e.g. "the blue beacon"
    alt: str           # a different fictional object of the same kind
    state: str         # adjective the subject can have
    group: str         # plural noun for scope claims
    items: str         # plural noun for counted items
    n: int             # exact count, 4-8 so n-2 and n+2 stay within NUMBER_WORDS
    day: str
    other_day: str
    cause: str
    effect: str
    condition: str

SCENARIOS = (
    Scenario("the blue beacon", "the red beacon", "active", "prototype units", "widgets", 5,
             "Tuesday", "Monday", "the alarm", "the shutdown", "the main switch is on"),
    Scenario("module C", "module D", "calibrated", "test cells", "samples", 6,
             "Wednesday", "Friday", "the power surge", "the reset", "the cover is closed"),
    Scenario("the north valve", "the south valve", "sealed", "pressure seals", "bolts", 4,
             "Thursday", "Saturday", "the leak", "the evacuation", "the pump is running"),
    Scenario("prototype Kestrel", "prototype Osprey", "airborne", "test flights", "batteries", 7,
             "Monday", "Sunday", "the gust", "the landing", "the wind is calm"),
    Scenario("relay unit seven", "relay unit nine", "online", "relay boards", "cables", 8,
             "Friday", "Tuesday", "the firmware update", "the outage", "the uplink is stable"),
    Scenario("sensor array four", "sensor array two", "operational", "sensor pods", "filters", 5,
             "Saturday", "Thursday", "the dust storm", "the recalibration", "the lens is clean"),
    Scenario("the cargo drone", "the survey drone", "charged", "delivery runs", "parcels", 6,
             "Sunday", "Wednesday", "the motor fault", "the abort", "the dock is free"),
    Scenario("test rig Alpha", "test rig Beta", "stable", "load trials", "weights", 4,
             "Monday", "Thursday", "the vibration", "the pause", "the clamps are tight"),
    Scenario("the backup pump", "the primary pump", "primed", "flow tests", "hoses", 7,
             "Tuesday", "Saturday", "the blockage", "the overflow", "the tank is full"),
    Scenario("station Lyra", "station Vega", "staffed", "night shifts", "crates", 8,
             "Wednesday", "Sunday", "the storm", "the delay", "the road is open"),
)
TEST_SCENARIOS = frozenset(range(7, 10))

def _cap(text: str) -> str:
    return text[0].upper() + text[1:]

def _w(n: int) -> str:
    return NUMBER_WORDS[n]

# (template id, category, label, explanation, builder(scenario) -> (claim, evidence)).
TEMPLATES = (
    # negation
    ("neg-reversal", "negation", C, "The evidence negates the claim.",
     lambda s: (f"{_cap(s.subj)} is {s.state}.", f"{_cap(s.subj)} is not {s.state}.")),
    ("neg-match", "negation", S, "The negative claim matches the evidence.",
     lambda s: (f"{_cap(s.subj)} is not {s.state}.", f"{_cap(s.subj)} is not {s.state}.")),
    ("neg-plain", "negation", S, "The positive claim matches the evidence.",
     lambda s: (f"{_cap(s.subj)} is {s.state}.", f"{_cap(s.subj)} is {s.state}.")),
    ("neg-no-longer", "negation", C, "'No longer' denies the present state.",
     lambda s: (f"{_cap(s.subj)} is {s.state}.", f"{_cap(s.subj)} is no longer {s.state}.")),
    # quantity
    ("qty-match", "quantity", S, "The count matches.",
     lambda s: (f"{_cap(s.subj)} used {_w(s.n)} {s.items}.", f"{_cap(s.subj)} used {_w(s.n)} {s.items}.")),
    ("qty-mismatch", "quantity", C, "A different exact count is given.",
     lambda s: (f"{_cap(s.subj)} used {_w(s.n + 2)} {s.items}.",
                f"{_cap(s.subj)} used exactly {_w(s.n)} {s.items}.")),
    ("qty-lower-bound", "quantity", S, "The exact count exceeds the claimed lower bound.",
     lambda s: (f"{_cap(s.subj)} used more than {_w(s.n - 2)} {s.items}.",
                f"{_cap(s.subj)} used exactly {_w(s.n)} {s.items}.")),
    ("qty-bound-violated", "quantity", C, "The exact count does not exceed the claimed bound.",
     lambda s: (f"{_cap(s.subj)} used more than {_w(s.n)} {s.items}.",
                f"{_cap(s.subj)} used exactly {_w(s.n)} {s.items}.")),
    ("qty-digits", "quantity", S, "Digits and number words state the same count.",
     lambda s: (f"{_cap(s.subj)} used {s.n} {s.items}.", f"{_cap(s.subj)} used {_w(s.n)} {s.items}.")),
    # uncertainty
    ("unc-may-always", "uncertainty", I, "Possibility does not establish 'always'.",
     lambda s: (f"{_cap(s.subj)} is always {s.state}.", f"{_cap(s.subj)} may be {s.state}.")),
    ("unc-might", "uncertainty", I, "A hedged statement does not establish the fact.",
     lambda s: (f"{_cap(s.subj)} is {s.state}.", f"{_cap(s.subj)} might be {s.state}.")),
    ("unc-unclear", "uncertainty", I, "The evidence states the matter is unresolved.",
     lambda s: (f"{_cap(s.subj)} is {s.state}.", f"It is unclear whether {s.subj} is {s.state}.")),
    ("unc-hedge-match", "uncertainty", S, "The hedged claim matches the hedged evidence.",
     lambda s: (f"{_cap(s.subj)} is possibly {s.state}.", f"{_cap(s.subj)} is possibly {s.state}.")),
    # scope
    ("scope-subset-open", "scope", I, "A subset does not establish a universal claim.",
     lambda s: (f"All {s.group} passed inspection.", f"Three {s.group} passed inspection.")),
    ("scope-subset-explicit", "scope", C, "The evidence says the rest failed.",
     lambda s: (f"All {s.group} passed inspection.",
                f"Only three {s.group} passed inspection, and the rest failed.")),
    ("scope-universal-to-some", "scope", S, "'All' entails 'some'.",
     lambda s: (f"Some {s.group} passed inspection.", f"All {s.group} passed inspection.")),
    ("scope-match", "scope", S, "The universal claim matches.",
     lambda s: (f"All {s.group} passed inspection.", f"All {s.group} passed inspection.")),
    # time
    ("time-other-open", "time", I, "Another day's status does not establish this day's.",
     lambda s: (f"{_cap(s.subj)} was {s.state} on {s.other_day}.", f"{_cap(s.subj)} was {s.state} on {s.day}.")),
    ("time-other-explicit", "time", C, "'Only' on another day excludes the claimed day.",
     lambda s: (f"{_cap(s.subj)} was {s.state} on {s.other_day}.",
                f"{_cap(s.subj)} was {s.state} only on {s.day}.")),
    ("time-match", "time", S, "The day matches.",
     lambda s: (f"{_cap(s.subj)} was {s.state} on {s.day}.", f"{_cap(s.subj)} was {s.state} on {s.day}.")),
    ("time-both-days", "time", S, "The evidence covers the claimed day.",
     lambda s: (f"{_cap(s.subj)} was {s.state} on {s.other_day}.",
                f"{_cap(s.subj)} was {s.state} on {s.other_day} and {s.day}.")),
    # entity
    ("ent-swap-open", "entity", I, "Evidence about another object does not establish this claim.",
     lambda s: (f"{_cap(s.subj)} passed the test.", f"{_cap(s.alt)} passed the test.")),
    ("ent-swap-explicit", "entity", C, "'Only' the other object excludes the claimed one.",
     lambda s: (f"{_cap(s.subj)} passed the test.", f"Only {s.alt} passed the test.")),
    ("ent-match", "entity", S, "The entity matches.",
     lambda s: (f"{_cap(s.subj)} passed the test.", f"{_cap(s.subj)} passed the test.")),
    ("ent-conjunction", "entity", S, "The conjunction includes the claimed object.",
     lambda s: (f"{_cap(s.subj)} passed the test.", f"Both {s.alt} and {s.subj} passed the test.")),
    # causality
    ("cause-sequence", "causality", I, "Sequence alone does not establish causality.",
     lambda s: (f"{_cap(s.cause)} caused {s.effect}.", f"{_cap(s.cause)} occurred before {s.effect}.")),
    ("cause-simultaneous", "causality", I, "Co-occurrence does not establish causality.",
     lambda s: (f"{_cap(s.cause)} caused {s.effect}.", f"{_cap(s.cause)} and {s.effect} happened at the same time.")),
    ("cause-denied", "causality", C, "The evidence denies the causal link.",
     lambda s: (f"{_cap(s.cause)} caused {s.effect}.", f"{_cap(s.cause)} did not cause {s.effect}.")),
    ("cause-match", "causality", S, "The evidence asserts the causal link.",
     lambda s: (f"{_cap(s.cause)} caused {s.effect}.", f"{_cap(s.cause)} caused {s.effect}.")),
    # conditional
    ("cond-unmet", "conditional", I, "A conditional does not establish its consequent.",
     lambda s: (f"{_cap(s.subj)} is {s.state}.", f"If {s.condition}, {s.subj} is {s.state}.")),
    ("cond-match", "conditional", S, "The conditional claim matches.",
     lambda s: (f"If {s.condition}, {s.subj} is {s.state}.", f"If {s.condition}, {s.subj} is {s.state}.")),
    ("cond-satisfied", "conditional", S, "The condition and its consequence are both asserted.",
     lambda s: (f"{_cap(s.subj)} is {s.state}.",
                f"{_cap(s.subj)} is {s.state} whenever {s.condition}, and {s.condition}.")),
    # paraphrase (tests lexical false alarms on supported claims)
    ("para-passive", "paraphrase", S, "Active and passive voice state the same event.",
     lambda s: (f"The crew inspected {s.subj}.", f"{_cap(s.subj)} was inspected by the crew.")),
    ("para-passive-negated", "paraphrase", C, "The passive evidence denies the event.",
     lambda s: (f"The crew inspected {s.subj}.", f"{_cap(s.subj)} was not inspected by the crew.")),
    # distractor (a similar sentence about another object sits beside the relevant one)
    ("distract-contradicted", "distractor", C, "The sentence about the claimed object negates it.",
     lambda s: (f"{_cap(s.subj)} is {s.state}.", f"{_cap(s.alt)} is {s.state}. {_cap(s.subj)} is not {s.state}.")),
    ("distract-supported", "distractor", S, "The sentence about the claimed object supports it.",
     lambda s: (f"{_cap(s.subj)} is {s.state}.", f"{_cap(s.alt)} is not {s.state}. {_cap(s.subj)} is {s.state}.")),
)

def expanded_examples(split: str = "all") -> tuple[AdversarialExample, ...]:
    if split not in ("all", "dev", "test"):
        raise ValueError("split must be 'all', 'dev' or 'test'")
    examples = []
    for index, scenario in enumerate(SCENARIOS):
        scenario_split = "test" if index in TEST_SCENARIOS else "dev"
        if split not in ("all", scenario_split):
            continue
        for template_id, category, label, explanation, build in TEMPLATES:
            claim, excerpt = build(scenario)
            example_id = f"{template_id}-s{index + 1:02d}"
            doc_id = "SYN-ADVX-" + example_id
            examples.append(AdversarialExample(example_id, category, Claim(claim, (doc_id,)),
                                               (_hit(doc_id, excerpt),), label, explanation,
                                               template_id, scenario_split))
    return tuple(examples)
