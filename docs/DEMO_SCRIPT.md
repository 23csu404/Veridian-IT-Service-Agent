# Demo Script

## 1. Introduction — 30 seconds
"This is the Veridian IT Service Agent. It converts natural-language employee IT requests into policy-grounded actions. The system can resolve, clarify, or escalate, and it creates a ticket with source and audit information."

## 2. Guest Wi-Fi — 45 seconds
Input: "Can I get Wi-Fi access for a guest visiting tomorrow?"
Show RESOLVE, KB-07, 24-hour credentials and no IT ticket requirement.

## 3. Password lockout — 45 seconds
Input: "I'm locked out of my account, tried my password 6 times."
Show ESCALATE → IT, KB-01, manual unlock.

## 4. Security incident — 60 seconds
Input: "I think I got a phishing email asking for my login."
Show HIGH priority, ESCALATE → Security, KB-09 and the security email. Emphasize that the agent does not claim to have sent the report.

## 5. Ambiguous request — 45 seconds
Input: "hey can you help, its not working"
Show CLARIFY and explain that the system refuses to guess.

## 6. Explain ticket/audit — 45 seconds
Show generated ticket, source, confidence and audit trail.

## 7. Show data — 30 seconds
Open Employee Requests, Ticket Queue and Knowledge Base tabs.

## 8. Close — 30 seconds
"Future production integration would connect this decision layer to ServiceNow/Jira, identity systems, employee directory and approved enterprise actions."
