import json
import streamlit as st

st.set_page_config(page_title="Scholarship Advisory System", page_icon="🎓", layout="wide")

DEFAULT_RULES = [
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
        "name": "Low CGPA – not eligible",
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
]

FIELDS = {
    "cgpa": "CGPA",
    "co_curricular_score": "Co-curricular score",
    "family_income": "Monthly family income (RM)",
    "community_service_hours": "Community service hours",
    "semester": "Current semester",
    "disciplinary_actions": "Disciplinary actions"
}
OPERATORS = {
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}

def validate_rules(rules):
    if not isinstance(rules, list):
        raise ValueError("The JSON root must be a list of rules.")
    for i, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            raise ValueError(f"Rule {i} must be a JSON object.")
        if not {"name", "priority", "conditions", "action"}.issubset(rule):
            raise ValueError(f"Rule {i} must contain name, priority, conditions and action.")
        if not isinstance(rule["priority"], (int, float)):
            raise ValueError(f"Rule {i}: priority must be numeric.")
        if not isinstance(rule["conditions"], list) or not rule["conditions"]:
            raise ValueError(f"Rule {i}: conditions must be a non-empty list.")
        if not isinstance(rule["action"], dict) or not {"decision", "reason"}.issubset(rule["action"]):
            raise ValueError(f"Rule {i}: action must contain decision and reason.")
        for condition in rule["conditions"]:
            if (not isinstance(condition, list) or len(condition) != 3
                    or condition[0] not in FIELDS or condition[1] not in OPERATORS
                    or not isinstance(condition[2], (int, float))):
                raise ValueError(f"Rule {i} has an invalid condition: {condition}")

def condition_matches(condition, facts):
    field, operator, threshold = condition
    return OPERATORS[operator](facts[field], threshold)

def evaluate_applicant(facts, rules):
    validate_rules(rules)
    # Highest priority is evaluated first. A rule fires only when ALL its conditions match.
    ordered_rules = sorted(rules, key=lambda rule: rule["priority"], reverse=True)
    for rule in ordered_rules:
        if all(condition_matches(condition, facts) for condition in rule["conditions"]):
            return {
                "decision": rule["action"]["decision"],
                "reason": rule["action"]["reason"],
                "matched_rule": rule["name"],
                "priority": rule["priority"],
            }
    return {
        "decision": "NO_MATCH",
        "reason": "No configured rule matched. Refer the application to the scholarship committee for manual review.",
        "matched_rule": "No matching rule",
        "priority": None,
    }

st.title("🎓 Scholarship Advisory System")
st.caption("A transparent rule-based decision-support prototype. Final scholarship decisions should be reviewed by the university committee.")

with st.sidebar:
    st.header("Applicant facts")
    cgpa = st.number_input("CGPA", min_value=0.0, max_value=4.0, value=3.50, step=0.01, format="%.2f")
    family_income = st.number_input("Monthly family income (RM)", min_value=0.0, value=3500.0, step=100.0)
    co_curricular_score = st.slider("Co-curricular involvement score", min_value=0, max_value=100, value=70)
    community_service_hours = st.number_input("Community service hours", min_value=0, value=20, step=1)
    semester = st.number_input("Current semester", min_value=1, max_value=20, value=3, step=1)
    disciplinary_actions = st.number_input("Number of disciplinary actions", min_value=0, value=0, step=1)

facts = {
    "cgpa": float(cgpa),
    "family_income": float(family_income),
    "co_curricular_score": int(co_curricular_score),
    "community_service_hours": int(community_service_hours),
    "semester": int(semester),
    "disciplinary_actions": int(disciplinary_actions),
}

st.subheader("Rule configuration (JSON editor)")
st.write("The default editor contains the five rules supplied in the lab sheet. You may edit the rule configuration for testing.")
default_json = json.dumps(DEFAULT_RULES, indent=2, ensure_ascii=False)
json_text = st.text_area("Edit rules JSON", value=default_json, height=420)

if st.button("Evaluate scholarship eligibility", type="primary"):
    try:
        parsed_rules = json.loads(json_text)
        result = evaluate_applicant(facts, parsed_rules)
        st.subheader("Decision result")
        if result["decision"] == "AWARD_FULL":
            st.success("Recommended decision: FULL SCHOLARSHIP")
        elif result["decision"] == "AWARD_PARTIAL":
            st.success("Recommended decision: PARTIAL SCHOLARSHIP")
        elif result["decision"] == "REVIEW":
            st.warning("Recommended decision: COMMITTEE REVIEW")
        elif result["decision"] == "REJECT":
            st.error("Recommended decision: NOT ELIGIBLE under the matched rule")
        else:
            st.info("Recommended decision: MANUAL REVIEW")
        st.write("**Matched rule:**", result["matched_rule"])
        st.write("**Reason:**", result["reason"])
        st.write("**Priority:**", result["priority"] if result["priority"] is not None else "N/A")
        st.write("**Applicant facts evaluated:**")
        st.json(facts)
    except json.JSONDecodeError as exc:
        st.error(f"Invalid JSON: {exc}")
    except (ValueError, KeyError, TypeError) as exc:
        st.error(f"Rule configuration error: {exc}")

with st.expander("How the rule-based system works"):
    st.markdown("""
    1. **Facts:** the applicant's entered information is stored as facts.
    2. **Rule base:** the JSON editor contains IF–THEN rules.
    3. **Inference:** conditions are checked; all conditions in a rule must match.
    4. **Priority:** rules are evaluated from highest to lowest priority, so the first matching rule determines the recommendation.
    5. **Output:** the app shows the decision, matched rule and reason.

    The supplied rules do not use community service hours or semester in their conditions. These facts are collected and displayed but do not affect the decision unless the committee adds a rule using them.
    """)