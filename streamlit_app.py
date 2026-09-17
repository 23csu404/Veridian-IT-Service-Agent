import streamlit as st
from agent.core import run_agent

st.set_page_config(
    page_title="Veridian IT Service Agent",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ Veridian IT Service Agent")
st.caption("AI-assisted internal IT support prototype")

st.markdown("""
This agent understands employee IT requests, matches them with the
supplied knowledge-base policies, and decides whether to **Resolve,
Clarify, or Escalate**.
""")

employee = st.text_input("Employee Name", "Demo Employee")
email = st.text_input("Employee Email", "employee@veridian-corp.example")

message = st.text_area(
    "Describe your IT issue",
    placeholder="Example: My account is locked after 6 failed password attempts."
)

if st.button("Analyze Request", type="primary"):
    if not message.strip():
        st.warning("Please enter an IT request.")
    else:
        result = run_agent(message)

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Intent", result.get("intent", "Unknown"))

        with col2:
            st.metric("Decision", result.get("action", "CLARIFY"))

        with col3:
            st.metric(
                "Policy Source",
                result.get("source_policy", "None")
            )

        st.subheader("Agent Response")

        if result.get("response"):
            st.write(result["response"])
        elif result.get("message"):
            st.write(result["message"])
        else:
            st.json(result)

        if result.get("policy"):
            st.subheader("Policy Used")
            st.info(str(result["policy"]))

        if result.get("audit"):
            st.subheader("Audit Trail")
            for item in result["audit"]:
                if isinstance(item, dict):
                    st.write(
                        f"**{item.get('time', '')}** — "
                        f"{item.get('event', '')}"
                    )
                else:
                    st.write(item)

st.divider()

st.caption(
    "Prototype uses the supplied Veridian IT policies only. "
    "It does not perform real account, security, or hardware actions."
)