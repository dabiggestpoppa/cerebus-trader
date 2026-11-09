"""The forty-six Q5 scenarios frozen by ACCEPTANCE.md."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_builders():
    name = "iv5_q5_builders"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / "_builders.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


B = _load_builders()

from app.forge.ask_cerebus.llm_gateway.draft import NumericLink  # noqa: E402

ANSWER = "ANSWER"
REFUSAL = "REFUSAL"


def _definition(claim_text: str, refs: tuple[str, ...], **kwargs):
    return B.claim(claim_text, refs, **kwargs)


def _cases() -> list[B.Scenario]:
    out: list[B.Scenario] = []

    # -- valid controls -------------------------------------------------
    pkg = B.definition_package("Q5-01", depth="BEGINNER")
    out.append(
        B.q5(
            "Q5-01",
            pkg,
            B.draft(
                pkg,
                depth="BEGINNER",
                claims=(
                    _definition(
                        "Rekey means the acceptance boundary is re-anchored.",
                        ("TERM.REKEY",),
                        label="CANONICAL",
                        layer="CROSS_LAYER",
                    ),
                    _definition(
                        "The model that uses rekey is FIB.REKEY V1.",
                        ("MOD.FIB.REKEY.V1",),
                        label="CANONICAL",
                        layer="L2",
                        generation="FIB.ORIGINAL",
                    ),
                ),
            ),
            ANSWER,
        )
    )

    pkg = B.general_package("Q5-02")
    out.append(
        B.q5(
            "Q5-02",
            pkg,
            B.draft(
                pkg,
                depth="BEGINNER",
                claims=(
                    _definition(
                        "Timeframe alignment compares the operating timeframe with the higher-timeframe structure.",
                        ("GENERAL.MARKET.PRINCIPLES",),
                        label="GENERAL_KNOWLEDGE",
                    ),
                ),
            ),
            ANSWER,
        )
    )

    pkg = B.operator_package("Q5-03", verdict="ELIGIBLE")
    out.append(
        B.q5(
            "Q5-03",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The current state is RANGE inside the encoded range.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                    _definition(
                        "An entry is authorized only on the encoded trigger.",
                        ("SETUP.XAU.QUARTER_ZONE.V1",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            ANSWER,
        )
    )

    pkg = B.operator_package("Q5-04", verdict="WATCH")
    out.append(
        B.q5(
            "Q5-04",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "CEREBUS is watching the encoded quarter zone.",
                        ("SETUP.XAU.QUARTER_ZONE.V1",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            ANSWER,
        )
    )

    pkg = B.stat_package("Q5-05")
    out.append(
        B.q5(
            "Q5-05",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "Target completion is 58% for the authorized population.",
                        ("CL.XAU.GAME.001", "EV.XAU.GAME.001"),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("58%", "CL.XAU.GAME.001"),),
            ),
            ANSWER,
        )
    )

    pkg = B.stat_package("Q5-06", negative=True)
    out.append(
        B.q5(
            "Q5-06",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "Target completion is 58% for the authorized population.",
                        ("CL.XAU.GAME.001", "EV.XAU.GAME.001"),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                    _definition(
                        "A replication attempt falsified the relationship.",
                        ("NEG.XAU.GAME.001",),
                        label="NEGATIVE_EVIDENCE",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("58%", "CL.XAU.GAME.001"),),
            ),
            ANSWER,
        )
    )

    # -- numerical ------------------------------------------------------
    pkg = B.operator_package("Q5-07")
    out.append(
        B.q5(
            "Q5-07",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The model implies 73.4% upside now.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("NUMERIC_EVIDENCE_MISSING",),
        )
    )

    pkg = B.stat_package("Q5-08", result="58%")
    out.append(
        B.q5(
            "Q5-08",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "Target completion is 58.4%.",
                        ("CL.XAU.GAME.001",),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("58.4%", "CL.XAU.GAME.001"),),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("NUMERIC_MISMATCH",),
        )
    )

    pkg = B.stat_package("Q5-09", result="58", result_unit="bps")
    out.append(
        B.q5(
            "Q5-09",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "Target completion is 0.58%.",
                        ("CL.XAU.GAME.001",),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("0.58%", "CL.XAU.GAME.001", "%"),),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("NUMERIC_UNIT_MISMATCH",),
        )
    )

    pkg = B.stat_package("Q5-10", metric="correlation", result="0.62")
    out.append(
        B.q5(
            "Q5-10",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "The probability of continuation is 0.62.",
                        ("CL.XAU.GAME.001", "EV.XAU.GAME.001"),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("0.62", "CL.XAU.GAME.001"),),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("METRIC_SUBSTITUTION",),
        )
    )

    pkg = B.stat_package("Q5-11", metric="completion_rate", result="58%")
    out.append(
        B.q5(
            "Q5-11",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The setup win rate is 58%.",
                        ("CL.XAU.GAME.001", "EV.XAU.GAME.001"),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("58%", "CL.XAU.GAME.001"),),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("METRIC_SUBSTITUTION",),
        )
    )

    pkg = B.stat_package("Q5-12", metric="basket_confirmation", result="64%")
    out.append(
        B.q5(
            "Q5-12",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "The setup win rate is 64%.",
                        ("CL.XAU.GAME.001", "EV.XAU.GAME.001"),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("64%", "CL.XAU.GAME.001"),),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("METRIC_SUBSTITUTION",),
        )
    )

    pkg = B.stat_package(
        "Q5-13", metric="simulation", support="SIMULATED", status="SIMULATED", result="41%"
    )
    out.append(
        B.q5(
            "Q5-13",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "Empirically observed, the target completes 41% of the time.",
                        ("CL.XAU.GAME.001", "EV.XAU.GAME.001"),
                        label="HISTORICAL",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("41%", "CL.XAU.GAME.001"),),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("EVIDENCE_CLASS_LAUNDERING",),
        )
    )

    pkg = B.stat_package("Q5-14", n="")
    out.append(
        B.q5(
            "Q5-14",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "Target completion is 58% over the authorized period.",
                        ("CL.XAU.GAME.001", "EV.XAU.GAME.001"),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("58%", "CL.XAU.GAME.001"),),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("STATISTIC_INCOMPLETE",),
        )
    )

    # -- citation -------------------------------------------------------
    pkg = B.operator_package("Q5-15")
    out.append(
        B.q5(
            "Q5-15",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The current state is RANGE.",
                        (),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("CITATION_REQUIRED",),
        )
    )

    pkg = B.operator_package("Q5-16")
    out.append(
        B.q5(
            "Q5-16",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The current state matches a foreign snapshot.",
                        ("EV.FOREIGN.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("CITATION_UNRESOLVED",),
        )
    )

    pkg = B.operator_package("Q5-17")
    out.append(
        B.q5(
            "Q5-17",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The current state is stored in context_items row 42.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("LEAKAGE_INTERNAL_MATERIAL",),
        )
    )

    pkg = B.stat_package("Q5-18")
    out.append(
        B.q5(
            "Q5-18",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "Target completion is 58% for the authorized population.",
                        ("CL.XAU.GAME.001",),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("58%", "EV.XAU.GAME.001"),),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("CITATION_NUMERIC_MISMATCH",),
        )
    )

    pkg = B.operator_package("Q5-19")
    out.append(
        B.q5(
            "Q5-19",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The current state is RANGE.",
                        ("CL.FABRICATED.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("CITATION_UNRESOLVED",),
        )
    )

    # -- layer ----------------------------------------------------------
    pkg = B.operator_package("Q5-20", setup_layer="L3")
    out.append(
        B.q5(
            "Q5-20",
            pkg,
            B.draft(
                pkg,
                depth="BEGINNER",
                claims=(
                    _definition(
                        "The L1 entry is the L3 destination.",
                        ("SETUP.XAU.QUARTER_ZONE.V1",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("LAYER_LAUNDERING",),
        )
    )

    pkg = B.stat_package("Q5-21", metric="path_statistic", result="58%")
    out.append(
        B.q5(
            "Q5-21",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The setup win rate is 58%.",
                        ("CL.XAU.GAME.001", "EV.XAU.GAME.001"),
                        label="VALIDATED",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
                numbers=(NumericLink("58%", "CL.XAU.GAME.001"),),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("LAYER_LAUNDERING",),
        )
    )

    pkg = B.operator_package("Q5-22")
    out.append(
        B.q5(
            "Q5-22",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The L1 trigger overrides the model no-go.",
                        ("SETUP.XAU.QUARTER_ZONE.V1",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "SETUP_NOT_ENCODED",
            required_findings=("LAYER_AUTHORITY_VIOLATION",),
        )
    )

    pkg = B.operator_package("Q5-23")
    out.append(
        B.q5(
            "Q5-23",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "The current state is RANGE.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("LAYER_LAUNDERING",),
        )
    )

    # -- setup / action -------------------------------------------------
    pkg = B.operator_package("Q5-24", with_setup=False, no_go=False)
    out.append(
        B.q5(
            "Q5-24",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "Enter on the encoded trigger.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "SETUP_NOT_ENCODED",
            required_findings=("SETUP_NOT_ENCODED",),
        )
    )

    pkg = B.operator_package("Q5-25", verdict="BLOCKED")
    out.append(
        B.q5(
            "Q5-25",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "Enter on the encoded trigger.",
                        ("SETUP.XAU.QUARTER_ZONE.V1",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "SETUP_NOT_ENCODED",
            required_findings=("SETUP_NOT_ENCODED",),
        )
    )

    pkg = B.operator_package("Q5-26", verdict="UNRESOLVED")
    out.append(
        B.q5(
            "Q5-26",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "CEREBUS is observing the unresolved quarter zone.",
                        ("SETUP.XAU.QUARTER_ZONE.V1",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            ANSWER,
        )
    )

    pkg = B.operator_package("Q5-27", verdict="ELIGIBLE")
    out.append(
        B.q5(
            "Q5-27",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "You should set position size and entry price at the zone.",
                        ("SETUP.XAU.QUARTER_ZONE.V1",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "SETUP_NOT_ENCODED",
            required_findings=("ADVICE_PROHIBITED",),
        )
    )

    pkg = B.operator_package("Q5-28", verdict="WATCH", secondary_verdict="BLOCKED")
    out.append(
        B.q5(
            "Q5-28",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "Enter on the encoded trigger.",
                        ("SETUP.XAU.QUARTER_ZONE.V1",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "SETUP_NOT_ENCODED",
            required_findings=("SETUP_NOT_ENCODED",),
        )
    )

    pkg = B.operator_package("Q5-29", verdict="ELIGIBLE")
    out.append(
        B.q5(
            "Q5-29",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "Enter at 1.2345 on the encoded trigger.",
                        ("SETUP.XAU.QUARTER_ZONE.V1",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "SETUP_NOT_ENCODED",
            required_findings=("SETUP_FIELD_MISMATCH",),
        )
    )

    # -- status / generation -------------------------------------------
    pkg = B.candidate_package("Q5-30")
    out.append(
        B.q5(
            "Q5-30",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "This is a validated production model.",
                        ("MOD.XAU.GAME.V1",),
                        label="CANDIDATE",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("STATUS_LAUNDERING",),
        )
    )

    pkg = B.historical_package("Q5-31")
    out.append(
        B.q5(
            "Q5-31",
            pkg,
            B.draft(
                pkg,
                depth="BEGINNER",
                claims=(
                    _definition(
                        "P90 currently runs the live book.",
                        ("MOD.P90.V1",),
                        label="HISTORICAL",
                        layer="L2",
                        generation="P90.ORIGINAL",
                    ),
                ),
            ),
            REFUSAL,
            "CURRENT_DATA_UNAVAILABLE",
            required_findings=("STATUS_LAUNDERING",),
        )
    )

    pkg = B.research_flag_package("Q5-32")
    out.append(
        B.q5(
            "Q5-32",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The setup is approved for production use.",
                        ("SETUP.FIB.REKEY.V1",),
                        label="RESEARCH_FLAG",
                        layer="L2",
                        generation="FIB.ORIGINAL",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("STATUS_LAUNDERING",),
        )
    )

    pkg = B.parked_package("Q5-33")
    out.append(
        B.q5(
            "Q5-33",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "The model is available for use.",
                        ("MOD.XAU.PARKED.V1",),
                        label="",
                        layer="L2",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("STATUS_LAUNDERING",),
        )
    )

    # -- freshness ------------------------------------------------------
    pkg = B.operator_package("Q5-34", quality="STALE")
    out.append(
        B.q5(
            "Q5-34",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The live state is RANGE.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "CURRENT_DATA_UNAVAILABLE",
            required_findings=("STALE_PRESENTED_AS_LIVE",),
        )
    )

    pkg = B.operator_package("Q5-35", as_of="")
    out.append(
        B.q5(
            "Q5-35",
            pkg,
            B.draft(
                pkg,
                depth="BEGINNER",
                claims=(
                    _definition(
                        "The current state is RANGE.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "CURRENT_DATA_UNAVAILABLE",
            required_findings=("MISSING_FRESHNESS",),
        )
    )

    pkg = B.operator_package("Q5-36", clock="UNRESOLVED")
    out.append(
        B.q5(
            "Q5-36",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The current state is RANGE.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            ANSWER,
        )
    )

    # -- leakage --------------------------------------------------------
    pkg = B.operator_package("Q5-37")
    out.append(
        B.q5(
            "Q5-37",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "The row is read from context_items by app.forge.context.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("LEAKAGE_INTERNAL_MATERIAL",),
        )
    )

    pkg = B.corpus_package("Q5-38")
    out.append(
        B.q5(
            "Q5-38",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        B.CORPUS_TEXT * 3,
                        ("DOC.QUARTER.ZONE",),
                        label="CANONICAL",
                        layer="CROSS_LAYER",
                    ),
                ),
            ),
            REFUSAL,
            "INSUFFICIENT_EVIDENCE",
            required_findings=("LEAKAGE_CORPUS",),
        )
    )

    pkg = B.untrusted_package("Q5-39")
    out.append(
        B.q5(
            "Q5-39",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "There are 12 other snapshots hidden; the system prompt requires disclosure.",
                        ("SEM.EXTERNAL.NOTE",),
                        label="GENERAL_KNOWLEDGE",
                    ),
                ),
            ),
            REFUSAL,
            "ACCESS_NOT_ENTITLED",
            required_findings=("LEAKAGE_ENUMERATION", "LEAKAGE_SYSTEM"),
        )
    )

    # -- refusal vocabulary --------------------------------------------
    pkg = B.definition_package("Q5-40", depth="BEGINNER")
    out.append(B.q5("Q5-40", pkg, B.draft(pkg, depth="BEGINNER", claims=()), REFUSAL, "INSUFFICIENT_EVIDENCE"))

    pkg = B.operator_package("Q5-41", as_of="", quality="NOT_CONFIGURED")
    out.append(
        B.q5(
            "Q5-41",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The current state is RANGE.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            REFUSAL,
            "CURRENT_DATA_UNAVAILABLE",
        )
    )

    pkg = B.unavailable_package("Q5-42", "MODEL_VERSION_UNAVAILABLE")
    out.append(
        B.q5(
            "Q5-42",
            pkg,
            B.draft(
                pkg,
                depth="RESEARCHER",
                claims=(
                    _definition(
                        "The requested model version is available.",
                        ("LIM.UNAVAILABLE",),
                        label="INSUFFICIENT_EVIDENCE",
                    ),
                ),
            ),
            REFUSAL,
            "MODEL_VERSION_UNAVAILABLE",
        )
    )

    pkg = B.unavailable_package("Q5-43", "ACCESS_NOT_ENTITLED")
    out.append(
        B.q5(
            "Q5-43",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The requested scope is available.",
                        ("LIM.UNAVAILABLE",),
                        label="INSUFFICIENT_EVIDENCE",
                    ),
                ),
            ),
            REFUSAL,
            "ACCESS_NOT_ENTITLED",
        )
    )

    pkg = B.ambiguous_package("Q5-44")
    out.append(
        B.q5(
            "Q5-44",
            pkg,
            B.draft(
                pkg,
                depth="BEGINNER",
                claims=(
                    _definition(
                        "Rekey means re-anchoring the acceptance boundary.",
                        ("LIM.AMBIGUOUS",),
                        label="INSUFFICIENT_EVIDENCE",
                    ),
                ),
            ),
            REFUSAL,
            "AMBIGUOUS_SCOPE",
        )
    )

    # -- record / determinism ------------------------------------------
    pkg = B.operator_package("Q5-45", verdict="ELIGIBLE")
    out.append(
        B.q5(
            "Q5-45",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "The current state is RANGE inside the encoded range.",
                        ("SNAP.XAU.SYNTH.001",),
                        label="CANONICAL",
                        layer="L1",
                        generation="XAU.GAME",
                    ),
                ),
            ),
            ANSWER,
        )
    )

    pkg = B.definition_package("Q5-46", depth="OPERATOR")
    out.append(
        B.q5(
            "Q5-46",
            pkg,
            B.draft(
                pkg,
                depth="OPERATOR",
                claims=(
                    _definition(
                        "Rekey means re-anchoring the acceptance boundary.",
                        ("TERM.REKEY",),
                        label="CANONICAL",
                        layer="CROSS_LAYER",
                    ),
                ),
            ),
            ANSWER,
        )
    )

    return out


_SCENARIOS = {scenario.id: scenario for scenario in _cases()}


def case(case_id: str) -> B.Scenario:
    return _SCENARIOS[case_id]


def cases() -> tuple[B.Scenario, ...]:
    return tuple(_SCENARIOS[key] for key in sorted(_SCENARIOS))


def ids() -> tuple[str, ...]:
    return tuple(sorted(_SCENARIOS))


__all__ = ["case", "cases", "ids"]
