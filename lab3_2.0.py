"""
BSD3513 Introduction to Artificial Intelligence - Lab Report 3
Chapter 3: Knowledge Representation System
Rule-Based Scholarship Advisory System (Streamlit)

Run locally:   streamlit run StudentID_Lab3.py
"""

import json
import operator

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# 1. KNOWLEDGE BASE: the rules EXACTLY as specified in the lab sheet
# ----------------------------------------------------------------------------
DEFAULT_RULES_JSON = """[
  {
    "name": "Top merit candidate",
    "priority": 100,
    "conditions": [
      ["cgpa", ">=", 3.7],
      ["co_curricular_score", ">=", 80],
      ["family_income", "<=", 8000],
      ["disciplinary_actions", "==", 0]
    ],
    "action": {
      "decision": "AWARD_FULL",
      "reason": "Excellent academic & co-curricular performance, with acceptable need"
    }
  },
  {
    "name": "Good candidate - partial scholarship",
    "priority": 80,
    "conditions": [
      ["cgpa", ">=", 3.3],
      ["co_curricular_score", ">=", 60],
      ["family_income", "<=", 12000],
      ["disciplinary_actions", "<=", 1]
    ],
    "action": {
      "decision": "AWARD_PARTIAL",
      "reason": "Good academic & involvement record with moderate need"
    }
  },
  {
    "name": "Need-based review",
    "priority": 70,
    "conditions": [
      ["cgpa", ">=", 2.5],
      ["family_income", "<=", 4000]
    ],
    "action": {
      "decision": "REVIEW",
      "reason": "High need but borderline academic score"
    }
  },
  {
    "name": "Low CGPA \u2013 not eligible",
    "priority": 95,
    "conditions": [
      ["cgpa", "<", 2.5]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "CGPA below minimum scholarship requirement"
    }
  },
  {
    "name": "Serious disciplinary record",
    "priority": 90,
    "conditions": [
      ["disciplinary_actions", ">=", 2]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "Too many disciplinary records"
    }
  }
]"""

# Fallback when no rule fires (not part of the given rule set)
DEFAULT_DECISION = {
    "decision": "NO_MATCH",
    "reason": "No rule matched the applicant's facts; refer to the committee.",
}

OPERATORS = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}

FACT_ORDER = [
    "cgpa",
    "family_income",
    "co_curricular_score",
    "community_service_hours",
    "semester",
    "disciplinary_actions",
]


# ----------------------------------------------------------------------------
# 2. RULE ENGINE (forward chaining + priority-based conflict resolution)
# ----------------------------------------------------------------------------
def validate_rules(rules):
    """Return a list of error strings; an empty list means the rules are valid."""
    errors = []
    if not isinstance(rules, list) or not rules:
        return ["Rules must be a non-empty JSON list."]
    for i, rule in enumerate(rules, start=1):
        label = f"Rule #{i}"
        if not isinstance(rule, dict):
            errors.append(f"{label}: must be an object.")
            continue
        for key in ("name", "priority", "conditions", "action"):
            if key not in rule:
                errors.append(f"{label}: missing key '{key}'.")
        if "priority" in rule and (
            isinstance(rule["priority"], bool)
            or not isinstance(rule["priority"], (int, float))
        ):
            errors.append(f"{label}: 'priority' must be a number.")
        conds = rule.get("conditions", [])
        if not isinstance(conds, list) or not conds:
            errors.append(f"{label}: 'conditions' must be a non-empty list.")
            conds = []
        for c in conds:
            if not (isinstance(c, list) and len(c) == 3):
                errors.append(f"{label}: condition {c} must be [field, op, value].")
            elif c[1] not in OPERATORS:
                errors.append(f"{label}: unsupported operator '{c[1]}'.")
        action = rule.get("action")
        if not isinstance(action, dict) or "decision" not in action:
            errors.append(f"{label}: 'action' must contain 'decision'.")
    return errors


def evaluate_condition(facts, condition):
    """Evaluate one [field, op, value] condition against the facts."""
    field, op, value = condition
    actual = facts.get(field)
    if actual is None:
        return False, actual
    try:
        return bool(OPERATORS[op](actual, value)), actual
    except TypeError:
        return False, actual


def evaluate_rule(facts, rule):
    """Return (all_conditions_met, per-condition trace)."""
    trace = []
    for cond in rule["conditions"]:
        ok, actual = evaluate_condition(facts, cond)
        trace.append(
            {"condition": f"{cond[0]} {cond[1]} {cond[2]}", "actual": actual, "met": ok}
        )
    return all(t["met"] for t in trace), trace


def run_engine(facts, rules):
    """
    Forward-chain over all rules. Every rule whose conditions are all satisfied
    is 'fired' (added to the conflict set). Conflict resolution picks the fired
    rule with the highest priority as the final decision.
    """
    fired, traces = [], {}
    for rule in rules:
        matched, trace = evaluate_rule(facts, rule)
        traces[rule["name"]] = trace
        if matched:
            fired.append(rule)
    fired.sort(key=lambda r: r["priority"], reverse=True)
    if fired:
        winner = fired[0]
        result = {
            "decision": winner["action"]["decision"],
            "reason": winner["action"].get("reason", ""),
            "rule": winner["name"],
        }
    else:
        result = {**DEFAULT_DECISION, "rule": "(default)"}
    return result, fired, traces


# ----------------------------------------------------------------------------
# 3. STREAMLIT USER INTERFACE
# ----------------------------------------------------------------------------
DECISION_STYLE = {
    "AWARD_FULL": ("success", "\U0001F3C6 Full scholarship awarded"),
    "AWARD_PARTIAL": ("success", "\U0001F396\uFE0F Partial scholarship awarded"),
    "REVIEW": ("warning", "\U0001F50D Refer for committee review"),
    "REJECT": ("error", "\u274C Not eligible"),
    "NO_MATCH": ("info", "\u2139\uFE0F No rule matched"),
}


def show_decision(result):
    kind, title = DECISION_STYLE.get(
        result["decision"], ("info", f"Decision: {result['decision']}")
    )
    getattr(st, kind)(f"**{title}** (`{result['decision']}`)")
    st.write(f"**Rule applied:** {result['rule']}")
    st.write(f"**Reason:** {result['reason']}")


def main():
    st.set_page_config(page_title="Scholarship Advisory (Rule-Based)", page_icon="\U0001F393", layout="wide")
    st.title("\U0001F393 Scholarship Advisory System")
    st.caption(
        "BSD3513 Introduction to Artificial Intelligence | "
        "Lab Report 3 | Loh Xiang Yi | SD24035"
    )

    st.caption(
        "Scholarship Advisory System - A transparent, rule-based decision "
        "support tool. Rules can be reviewed and edited in the "
        "sidebar JSON editor."
    )

    # ---- Sidebar: JSON rule editor -------------------------------------
    st.sidebar.header("\u2699\uFE0F Rule configuration")
    if "rules_text" not in st.session_state:
        st.session_state.rules_text = DEFAULT_RULES_JSON
    if st.sidebar.button("Reset to default rules"):
        st.session_state.rules_text = DEFAULT_RULES_JSON
        st.session_state.pop("editor", None)
    rules_text = st.sidebar.text_area(
        "Rules (JSON)", value=st.session_state.rules_text, height=520, key="editor"
    )
    st.session_state.rules_text = rules_text

    rules, rule_errors = None, []
    try:
        rules = json.loads(rules_text)
        rule_errors = validate_rules(rules)
    except json.JSONDecodeError as exc:
        rule_errors = [f"Invalid JSON: {exc}"]

    if rule_errors:
        st.sidebar.error("Rule set is invalid:\n\n" + "\n".join(f"- {e}" for e in rule_errors))
    else:
        st.sidebar.success(f"{len(rules)} rules loaded.")

    tab_single, tab_batch, tab_kb = st.tabs(
        ["\U0001F9D1\u200D\U0001F393 Single applicant", "\U0001F4C4 Batch (CSV)", "\U0001F4DA Knowledge base"]
    )

    # ---- Tab 1: single applicant ---------------------------------------
    with tab_single:
        st.subheader("Applicant facts")
        c1, c2, c3 = st.columns(3)
        cgpa = c1.number_input("Cumulative GPA (CGPA)", 0.0, 4.0, 3.5, 0.01)
        income = c2.number_input("Monthly family income (RM)", 0, 100000, 5000, 100)
        cocu = c3.slider("Co-curricular score (0\u2013100)", 0, 100, 70)
        c4, c5, c6 = st.columns(3)
        service = c4.number_input("Community service hours", 0, 1000, 20, 1)
        semester = c5.number_input("Current semester", 1, 14, 3, 1)
        disc = c6.number_input("Disciplinary actions on record", 0, 20, 0, 1)

        facts = {
            "cgpa": cgpa,
            "family_income": income,
            "co_curricular_score": cocu,
            "community_service_hours": service,
            "semester": semester,
            "disciplinary_actions": disc,
        }

        if st.button("Evaluate applicant", type="primary", disabled=bool(rule_errors)):
            result, fired, traces = run_engine(facts, rules)
            show_decision(result)

            st.markdown("#### Why? (explanation trace)")
            if fired:
                st.write(
                    "Rules fired (highest priority wins): "
                    + ", ".join(f"**{r['name']}** (p={r['priority']})" for r in fired)
                )
            else:
                st.write("No rules fired.")
            for rule in sorted(rules, key=lambda r: r["priority"], reverse=True):
                icon = "\u2705" if rule in fired else "\u274C"
                with st.expander(f"{icon} {rule['name']} \u2013 priority {rule['priority']}"):
                    st.dataframe(pd.DataFrame(traces[rule["name"]]), hide_index=True)

    # ---- Tab 2: batch evaluation ---------------------------------------
    with tab_batch:
        st.subheader("Evaluate many applicants")
        st.write(
            "Upload a CSV with columns: `cgpa, family_income, co_curricular_score, "
            "community_service_hours, semester, disciplinary_actions`."
        )
        sample = pd.DataFrame(
            [
                [3.85, 6000, 90, 40, 4, 0],
                [3.40, 10000, 65, 25, 3, 1],
                [2.80, 3000, 40, 10, 2, 0],
                [2.20, 2000, 70, 15, 2, 0],
                [3.90, 5000, 95, 60, 5, 2],
            ],
            columns=FACT_ORDER,
        )
        st.download_button("Download sample CSV", sample.to_csv(index=False), "sample_applicants.csv", "text/csv")
        upload = st.file_uploader("Upload applicants CSV", type="csv")
        df = pd.read_csv(upload) if upload else sample
        if not upload:
            st.info("Showing the built-in sample applicants.")
        if rule_errors:
            st.warning("Fix the rule set to run the batch evaluation.")
        else:
            outputs = []
            for _, row in df.iterrows():
                res, _, _ = run_engine(row.to_dict(), rules)
                outputs.append(res)
            out = df.copy()
            out["decision"] = [o["decision"] for o in outputs]
            out["rule"] = [o["rule"] for o in outputs]
            out["reason"] = [o["reason"] for o in outputs]
            st.dataframe(out, hide_index=True)
            st.bar_chart(out["decision"].value_counts())
            st.download_button("Download results", out.to_csv(index=False), "results.csv", "text/csv")

    # ---- Tab 3: knowledge base overview --------------------------------
    with tab_kb:
        st.subheader("Current rule base (IF conditions THEN action)")
        if rule_errors:
            st.warning("Rule set is invalid; see the sidebar.")
        else:
            for rule in sorted(rules, key=lambda r: r["priority"], reverse=True):
                conds = " AND ".join(f"`{c[0]} {c[1]} {c[2]}`" for c in rule["conditions"])
                st.markdown(
                    f"**{rule['name']}** (priority {rule['priority']})  \n"
                    f"IF {conds}  \nTHEN **{rule['action']['decision']}** \u2013 {rule['action'].get('reason', '')}"
                )
            st.caption(
                "Conflict resolution: when several rules fire, the one with the highest priority is used."
            )


if __name__ == "__main__":
    main()