
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PATHS AND DATA
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "data" / "policies.json"

with open(POLICY_PATH, encoding="utf-8") as f:
    POLICIES = json.load(f)


# ============================================================
# INTENT DEFINITIONS
# ============================================================

INTENTS = {
    "security_incident": [
        "phishing",
        "malware",
        "unauthorized access",
        "suspicious email",
        "credential theft",
        "login email",
    ],

    "guest_wifi": [
        "guest wifi",
        "guest wi-fi",
        "visitor wifi",
        "visitor wi-fi",
        "guest access",
    ],

    "password_lockout": [
        "locked out",
        "password",
        "failed attempts",
        "wrong password",
        "account locked",
    ],

    "vpn": [
        "vpn",
        "credentials expired",
        "vpn credentials",
    ],

    "software_install": [
        "install",
        "installation",
        "software",
        "browser extension",
        "extension",
        "data-analysis tool",
    ],

    "printer": [
        "printer",
        "printing",
        "paper jam",
        "print spooler",
        "print queue",
    ],

    "mailbox": [
        "mailbox",
        "email full",
        "quota",
        "can't send emails",
        "cannot send emails",
    ],

    "expense": [
        "expense tool",
        "expense software",
        "expense management",
        "expense login",
    ],

    "wfh_equipment": [
        "work from home",
        "working from home",
        "remote",
        "monitor",
        "home office equipment",
        "chair",
    ],

    "laptop": [
        "laptop",
        "screen flickering",
        "computer won't turn on",
        "computer dead",
        "hardware failure",
    ],

    "admin_access": [
        "admin access",
        "administrator access",
        "server access",
        "finance reporting server",
    ],
}


# ============================================================
# INTENT -> SUPPLIED POLICY
# ============================================================

INTENT_TO_POLICIES = {
    "security_incident": ["KB-09"],
    "guest_wifi": ["KB-07"],
    "password_lockout": ["KB-01"],
    "vpn": ["KB-02"],
    "software_install": ["KB-04"],
    "printer": ["KB-05"],
    "mailbox": ["KB-06"],
    "expense": ["KB-08"],
    "wfh_equipment": ["KB-10"],
    "laptop": ["KB-03", "ASSET-POLICY"],
    "admin_access": [],
}


# ============================================================
# POLICY RETRIEVER
# ============================================================

class PolicyRetriever:

    def __init__(self, policies):
        self.policies = policies

        corpus = [
            f"{p['title']} {p['category']} {p['text']}"
            for p in policies
        ]

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query, top_k=3):

        q = self.vectorizer.transform([query])

        scores = cosine_similarity(q, self.matrix)[0]

        idxs = scores.argsort()[::-1][:top_k]

        return [
            {
                "policy": self.policies[i],
                "score": round(float(scores[i]), 3)
            }
            for i in idxs
        ]


RETRIEVER = PolicyRetriever(POLICIES)


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_intent(text: str) -> tuple[str, float]:

    t = text.lower()

    matches = []

    for intent, terms in INTENTS.items():

        score = sum(
            1 for term in terms
            if term in t
        )

        # Guest Wi-Fi can be written as:
        # "Wi-Fi access for a guest"
        if (
            intent == "guest_wifi"
            and ("wi-fi" in t or "wifi" in t)
            and "guest" in t
        ):
            score += 2

        if score:
            matches.append((intent, score))

    if not matches:
        return "unknown", 0.0

    matches.sort(
        key=lambda x: x[1],
        reverse=True
    )

    best = matches[0][1]

    confidence = min(
        0.99,
        0.60 + 0.12 * (best - 1)
    )

    if best == 1 and len(matches) > 1:
        confidence = 0.68

    return matches[0][0], round(confidence, 2)


# ============================================================
# ENTITY EXTRACTION
# ============================================================

def extract_entities(text: str) -> dict:

    t = text.lower()

    out = {}

    # --------------------------------------------------------
    # DEVICE AGE
    # Examples:
    # "3.5 years"
    # "3 years old"
    # "had it about 3.5 years"
    # --------------------------------------------------------

    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        t
    )

    if m:
        out["device_age_years"] = float(m.group(1))


    # --------------------------------------------------------
    # FAILED PASSWORD ATTEMPTS
    #
    # Handles:
    # "6 attempts"
    # "6 failed attempts"
    # "6 failed password attempts"
    # "password 6 times"
    # "tried my password 6 times"
    # --------------------------------------------------------

    m = re.search(
        r"(\d+)\s*(?:failed\s+)?(?:password\s+)?(?:times?|attempts?)",
        t
    )

    if m and any(
        x in t
        for x in [
            "password",
            "attempt",
            "tried",
        ]
    ):
        out["failed_attempts"] = int(m.group(1))


    # --------------------------------------------------------
    # EMPLOYEE TYPE
    # --------------------------------------------------------

    if "contractor" in t:

        out["employee_type"] = "contractor"

    elif (
        "full-time" in t
        or "full time" in t
    ):

        out["employee_type"] = "full-time"


    # --------------------------------------------------------
    # REMOTE DAYS PER WEEK
    #
    # Examples:
    # "4 days a week"
    # "4 days per week"
    # --------------------------------------------------------

    m = re.search(
        r"(\d+)\s*days?\s*(?:a|per)\s*week",
        t
    )

    if m:
        out["remote_days_per_week"] = int(m.group(1))


    return out


# ============================================================
# POLICY LOOKUP
# ============================================================

def _policy(policy_id):

    return next(
        (
            p for p in POLICIES
            if p["id"] == policy_id
        ),
        None
    )


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent(text: str) -> dict:

    intent, confidence = detect_intent(text)

    entities = extract_entities(text)

    retrieved = RETRIEVER.search(text)

    source_ids = INTENT_TO_POLICIES.get(
        intent,
        []
    )

    source_policies = [
        _policy(x)
        for x in source_ids
        if _policy(x)
    ]

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    audit = [
        {
            "time": now,
            "event": "Request received"
        },

        {
            "time": now,
            "event": f"Intent detected: {intent}",
            "detail": f"confidence={confidence}"
        },

        {
            "time": now,
            "event": "Entities extracted",
            "detail": (
                json.dumps(entities)
                if entities
                else "none"
            )
        },
    ]


    # --------------------------------------------------------
    # RESULT HELPER
    # --------------------------------------------------------

    def result(
        action,
        response,
        department,
        priority,
        status,
        source=None,
        follow_up=None
    ):

        audit2 = list(audit)

        audit2.append(
            {
                "time": now,
                "event": f"Decision: {action}"
            }
        )

        audit2.append(
            {
                "time": now,
                "event": f"Routing: {department}"
            }
        )

        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "action": action,
            "response": response,
            "department": department,
            "priority": priority,
            "status": status,
            "source": source,
            "follow_up": follow_up,
            "retrieval": retrieved,
            "audit": audit2,
        }


    # ========================================================
    # UNKNOWN / AMBIGUOUS
    # ========================================================

    if intent == "unknown":

        return result(
            "CLARIFY",

            (
                "I need a little more information before "
                "I can route this correctly. What isn't "
                "working, and which IT service or device "
                "is affected (for example: laptop, VPN, "
                "password/account, printer, email, "
                "software, or another service)?"
            ),

            "IT",
            "Medium",
            "Needs clarification"
        )


    # ========================================================
    # KB-09 SECURITY INCIDENT
    # ========================================================

    if intent == "security_incident":

        return result(
            "ESCALATE",

            (
                "This is a potential security incident. "
                "Report it immediately to "
                "security@veridian-corp.example. "
                "Do not forward the suspicious email "
                "to other employees. This case is routed "
                "to Security for human handling."
            ),

            "Security",
            "High",
            "Open / Routed",
            _policy("KB-09")
        )


    # ========================================================
    # KB-07 GUEST WI-FI
    # ========================================================

    if intent == "guest_wifi":

        return result(
            "RESOLVE",

            (
                "Guest Wi-Fi credentials are valid for "
                "24 hours and can be generated by any "
                "employee from the front-desk kiosk. "
                "No IT ticket is required."
            ),

            "IT",
            "Low",
            "Resolved",
            _policy("KB-07")
        )


    # ========================================================
    # KB-01 PASSWORD RESET / LOCKOUT
    # ========================================================

    if intent == "password_lockout":

        attempts = entities.get(
            "failed_attempts"
        )

        # We need the number of attempts
        # before deciding the correct path.

        if attempts is None:

            return result(
                "CLARIFY",

                (
                    "How many failed password attempts "
                    "have you made? The supplied policy "
                    "requires manual IT unlock after "
                    "5 failed attempts."
                ),

                "IT",
                "Medium",
                "Needs clarification",
                _policy("KB-01")
            )

        # IMPORTANT:
        # KB-01 says AFTER 5 FAILED ATTEMPTS,
        # contact IT for manual unlock.
        #
        # Therefore 5 or more = escalation.

        if attempts >= 5:

            return result(
                "ESCALATE",

                (
                    f"You reported {attempts} failed "
                    "password attempts. KB-01 states "
                    "that after 5 failed attempts, IT "
                    "must manually unlock the account. "
                    "No approval is required. This case "
                    "is routed to IT."
                ),

                "IT",
                "Medium",
                "Open / Routed",
                _policy("KB-01")
            )

        return result(
            "RESOLVE",

            (
                "You can reset your password through "
                "the self-service portal at any time. "
                "If you become locked out after 5 "
                "failed attempts, IT must manually "
                "unlock the account."
            ),

            "IT",
            "Medium",
            "Resolved",
            _policy("KB-01")
        )


    # ========================================================
    # KB-02 VPN
    # ========================================================

    if intent == "vpn":

        if entities.get("employee_type") == "contractor":

            return result(
                "ESCALATE",

                (
                    "For contractors, VPN access requires "
                    "manager approval submitted through "
                    "the access request form. I cannot "
                    "approve access directly, so this case "
                    "follows the manager-approval route."
                ),

                "IT / Manager approval",
                "Medium",
                "Open / Routed",
                _policy("KB-02")
            )

        return result(
            "RESOLVE",

            (
                "VPN access is granted automatically to "
                "full-time employees. VPN credentials "
                "expire every 90 days and must be renewed "
                "by the employee. If your credentials "
                "have expired, renew them; if the issue "
                "persists, route it to IT."
            ),

            "IT",
            "Medium",
            "Resolved",
            _policy("KB-02")
        )


    # ========================================================
    # KB-04 SOFTWARE INSTALLATION
    # ========================================================

    if intent == "software_install":

        t = text.lower()

        if (
            "not in" in t
            or "non-catalog" in t
            or "browser extension" in t
            or "extension" in t
        ):

            return result(
                "ESCALATE",

                (
                    "This software/extension is described "
                    "as outside the approved catalog, so "
                    "IT Security review is required. "
                    "The supplied policy states that "
                    "review takes 3–5 business days. "
                    "This case is routed to IT Security."
                ),

                "IT Security",
                "Medium",
                "Open / Routed",
                _policy("KB-04")
            )

        return result(
            "RESOLVE",

            (
                "Standard software listed in the "
                "approved catalog can be self-installed. "
                "If the software is not in the catalog, "
                "IT Security review is required."
            ),

            "IT",
            "Low",
            "Resolved",
            _policy("KB-04")
        )


    # ========================================================
    # KB-05 PRINTER
    # ========================================================

    if intent == "printer":

        return result(
            "RESOLVE",

            (
                "First check the printer queue and "
                "restart the print spooler. If the issue "
                "persists after restart, log a ticket and "
                "include the printer's asset tag."
            ),

            "IT",
            "Medium",
            "Resolved",
            _policy("KB-05")
        )


    # ========================================================
    # KB-06 MAILBOX
    # ========================================================

    if intent == "mailbox":

        return result(
            "RESOLVE",

            (
                "The default mailbox quota is 25GB. "
                "If your mailbox is nearing/full, "
                "archive old mail. A quota increase "
                "beyond 25GB requires manager approval "
                "and is capped at 50GB."
            ),

            "IT",
            "Medium",
            "Resolved",
            _policy("KB-06")
        )


    # ========================================================
    # KB-08 EXPENSE SOFTWARE
    # ========================================================

    if intent == "expense":

        return result(
            "CLARIFY",

            (
                "Access to the expense management tool "
                "is granted by Finance, not IT. IT can "
                "assist with login/technical issues once "
                "an account already exists. Please confirm "
                "whether your expense account already exists."
            ),

            "Finance / IT",
            "Medium",
            "Needs clarification",
            _policy("KB-08")
        )


    # ========================================================
    # KB-10 WORK FROM HOME EQUIPMENT
    # ========================================================

    if intent == "wfh_equipment":

        days = entities.get(
            "remote_days_per_week"
        )

        if days is not None and days > 3:

            return result(
                "ESCALATE",

                (
                    "Working remotely more than 3 days "
                    "per week makes you eligible for the "
                    "one-time home-office equipment "
                    "allowance. Manager sign-off and "
                    "Finance processing are required; "
                    "IT handles equipment shipping only "
                    "after approval."
                ),

                "Manager / Finance / IT",
                "Medium",
                "Open / Routed",
                _policy("KB-10")
            )

        return result(
            "CLARIFY",

            (
                "How many days per week are you working "
                "remotely? The supplied policy applies "
                "to employees working remotely more than "
                "3 days per week."
            ),

            "Manager / Finance / IT",
            "Medium",
            "Needs clarification",
            _policy("KB-10")
        )


    # ========================================================
    # KB-03 LAPTOP REPLACEMENT + ASSET POLICY
    # ========================================================

    if intent == "laptop":

        age = entities.get(
            "device_age_years"
        )

        # Under 3 years:
        # normal replacement eligibility is not met.
        # Earlier replacement is allowed only for
        # verified hardware failure.

        if age is not None and age < 3:

            return result(
                "ESCALATE",

                (
                    "The laptop is under 3 years old, "
                    "so the normal replacement threshold "
                    "is not met. KB-03 allows earlier "
                    "replacement in case of verified "
                    "hardware failure. I have routed this "
                    "to IT for hardware verification rather "
                    "than assuming replacement is approved."
                ),

                "IT / Hardware verification",
                "Medium",
                "Open / Routed",
                _policy("KB-03")
            )

        # 3 years or more:
        # KB-03 makes it eligible.
        #
        # However, the Asset Management Policy states
        # that the standard refresh cycle is 4 years.
        # Replacement before 4 years requires Finance
        # sign-off in addition to IT approval.

        if age is not None and age >= 3:

            return result(
                "ESCALATE",

                (
                    "The laptop has reached at least "
                    "3 years of service, which meets "
                    "KB-03's replacement eligibility "
                    "condition. Requests must be raised "
                    "at least 2 weeks before intended "
                    "replacement. Because the standard "
                    "hardware refresh cycle is 4 years, "
                    "replacement before 4 years also "
                    "requires Finance sign-off in addition "
                    "to IT approval. I have routed this "
                    "for review."
                ),

                "IT / Finance & Assets",
                "Medium",
                "Open / Routed",
                _policy("KB-03")
            )

        return result(
            "CLARIFY",

            (
                "I need the device age and whether there "
                "is a verified hardware failure to assess "
                "replacement under the supplied policy. "
                "I will not assume replacement approval."
            ),

            "IT",
            "Medium",
            "Needs clarification",
            _policy("KB-03")
        )


    # ========================================================
    # ADMIN ACCESS
    # ========================================================

    if intent == "admin_access":

        return result(
            "ESCALATE",

            (
                "The supplied data does not define an "
                "approval policy for administrative access "
                "to the finance reporting server. I will "
                "not invent an approval path. This request "
                "requires human review and routing to the "
                "appropriate owner."
            ),

            "Human IT / Appropriate owner",
            "High",
            "Open / Routed"
        )


    # ========================================================
    # FALLBACK
    # ========================================================

    return result(
        "CLARIFY",

        "I need more information to determine the correct IT workflow.",

        "IT",
        "Medium",
        "Needs clarification"
    )