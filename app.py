import streamlit as st
import numpy as np
import pandas as pd

from database import (
    get_approved_facts,
    get_pending_facts,
    add_approved_fact,
    review_fact,
    initialize_database,
    save_verification,
    get_verification_history,
)

from verifier import verify_claim

st.set_page_config(
    page_title="ClaimGuard | Brand Governance",
    page_icon="🛡️",
    layout="wide",
)

initialize_database()

st.title("🛡️ ClaimGuard")
st.subheader("Evidence-first brand governance")
st.write(
    "Verify marketing claims against approved company facts "
    "before publication."
)

st.info(
    "Research prototype. Results depend on the approved facts "
    "entered into the database."
)

company = st.text_input(
    "Company name",
    value="Demo Health Foods",
)

claim = st.text_area(
    "Enter the claim you want to verify",
    placeholder="Example: Each serving contains 10 grams of protein.",
    height=120,
)

if st.button("Verify claim", type="primary"):
    if not company.strip():
        st.warning("Please enter a company name.")
    elif not claim.strip():
        st.warning("Please enter a claim.")
    else:
        result = verify_claim(claim, company.strip())

        # Save this verification in the database
        save_verification(
            company_name=company.strip(),
            claim_text=claim.strip(),
            verification_status=result["status"],
            reason=result["reason"],
        )

        st.divider()
        st.subheader("Verification result")

        status = result["status"]

        if status == "SUPPORTED":
            st.success("SUPPORTED")
        elif status == "CONTRADICTED":
            st.error("CONTRADICTED")
        else:
            st.warning("UNVERIFIABLE")

        st.write(result["reason"])

        st.subheader("Evidence assessment")

        if result["status"] == "SUPPORTED":
            st.info(
                "Exact text match: the claim matches an approved fact. "
                "The real-world accuracy of the source has not been "
                "independently verified."
            )
        elif result["status"] == "CONTRADICTED":
            st.warning(
                "Conflict found: the claim differs numerically from "
                "an approved fact with matching wording. Review the "
                "source before making a final decision."
            )
        else:
            st.info(
                "Insufficient evidence: no clear match or supported "
                "conflict was found. This does not mean the claim is false."
            )

        if result["evidence"]:
            st.subheader("Matching approved evidence")

            for item in result["evidence"]:
                st.write("**Approved fact:**", item["fact_text"])
                st.write("**Evidence source:**", item["evidence_source"])
        else:
            st.caption(
                "No matching approved evidence was returned. "
                "The claim has not been proven false."
            )

st.divider()
st.subheader("Approved facts library")

st.divider()
st.header("Add an Approved Fact")
st.write(
    "Submit a fact for review. New facts remain pending "
    "until a reviewer approves them."
)

with st.form("add_fact_form"):
    new_company = st.text_input("Company name")
    new_fact = st.text_area("Factual statement")
    new_source = st.text_input("Evidence source")

    submitted = st.form_submit_button("Submit for review")

    if submitted:
        if not all(
            value.strip()
            for value in (new_company, new_fact, new_source)
        ):
            st.error("Please complete all fields.")
        else:
            add_approved_fact(
                new_company,
                new_fact,
                new_source,
            )
            st.success("Fact submitted for review.")
            st.rerun()


st.divider()
st.header("Pending Facts Review")

pending_facts = get_pending_facts()

if not pending_facts:
    st.info("There are no pending facts to review.")
else:
    for item in pending_facts:
        with st.expander(
            f"Fact #{item['id']} — {item['company_name']}"
        ):
            st.write("**Statement:**", item["fact_text"])
            st.write("**Evidence source:**", item["evidence_source"])

            st.warning(
                "Check the original evidence before approving this fact."
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Approve",
                    key=f"approve_{item['id']}",
                ):
                    review_fact(item["id"], "APPROVED")
                    st.success("Fact approved.")
                    st.rerun()

            with col2:
                if st.button(
                    "Reject",
                    key=f"reject_{item['id']}",
                ):
                    review_fact(item["id"], "REJECTED")
                    st.warning("Fact rejected.")
                    st.rerun()

if company.strip():
    facts = get_approved_facts(company.strip())

    if facts:
        for item in facts:
            with st.expander(f"Fact #{item['id']}"):
                st.write("**Fact:**", item["fact_text"])
                st.write("**Source:**", item["evidence_source"])
    else:
        st.write("No approved facts found for this company.")

# ClaimGuard Summary Dashboard
st.divider()
st.header("ClaimGuard Dashboard")
st.caption("Summary of recorded claim verification checks.")

history = get_verification_history(limit=50)

total_checks = len(history)
supported_count = sum(
    1 for record in history
    if record["verification_status"] == "SUPPORTED"
)
contradicted_count = sum(
    1 for record in history
    if record["verification_status"] == "CONTRADICTED"
)
unverifiable_count = sum(
    1 for record in history
    if record["verification_status"] == "UNVERIFIABLE"
)

col1, col2 = st.columns(2)

with col1:
    st.metric("Total checks (latest 50)", total_checks)
    st.metric("Supported", supported_count)

with col2:
    st.metric("Contradicted", contradicted_count)
    st.metric("Unverifiable", unverifiable_count)

# Verification status chart
st.subheader("Verification Status Distribution")

chart_data = pd.DataFrame({
    "Status": [
        "Supported",
        "Contradicted",
        "Unverifiable",
    ],
    "Count": [
        supported_count,
        contradicted_count,
        unverifiable_count,
    ],
})

st.bar_chart(
    chart_data,
    x="Status",
    y="Count",
)

# Verification status percentages
st.subheader("Verification Status Percentages")

if total_checks > 0:
    supported_pct = supported_count / total_checks * 100
    contradicted_pct = contradicted_count / total_checks * 100
    unverifiable_pct = unverifiable_count / total_checks * 100

    pct1, pct2, pct3 = st.columns(3)

    with pct1:
        st.metric(
            "Supported (%)",
            f"{supported_pct:.1f}%",
        )

    with pct2:
        st.metric(
            "Contradicted (%)",
            f"{contradicted_pct:.1f}%",
        )

    with pct3:
        st.metric(
            "Unverifiable (%)",
            f"{unverifiable_pct:.1f}%",
        )
else:
    st.info("Percentages will appear after the first verification check.")

st.caption(
    "Percentages reflect recorded verification results, "
    "not independently measured claim accuracy."
)

# Verification History — independent of the facts library
st.divider()
st.header("Verification History")
st.caption("Your 50 most recent verification checks.")

history = get_verification_history(limit=50)

if history:
    # Filter controls
    col1, col2 = st.columns(2)

    with col1:
        status_options = [
            "All",
            "SUPPORTED",
            "CONTRADICTED",
            "UNVERIFIABLE",
        ]
        selected_status = st.selectbox(
            "Filter by status",
            status_options,
        )

    with col2:
        company_options = ["All"] + sorted(
            set(record["company_name"] for record in history)
        )
        selected_company = st.selectbox(
            "Filter by company",
            company_options,
        )

    search_text = st.text_input(
        "Search claim text",
        placeholder="Enter words from a claim...",
    )

    filtered_history = history

    if selected_status != "All":
        filtered_history = [
            record for record in filtered_history
            if record["verification_status"] == selected_status
        ]

    if selected_company != "All":
        filtered_history = [
            record for record in filtered_history
            if record["company_name"] == selected_company
        ]

    if search_text.strip():
        filtered_history = [
            record for record in filtered_history
            if search_text.casefold()
            in record["claim_text"].casefold()
        ]

    st.caption(
        f"Showing {len(filtered_history)} of {len(history)} records."
    )

    if filtered_history:
        for record in filtered_history:
            with st.expander(
                f"#{record['id']} — {record['verification_status']} "
                f"| {record['company_name']} "
                f"| {record['created_at']}"
            ):
                st.write("**Claim:**", record["claim_text"])
                st.write("**Result:**", record["verification_status"])
                st.write("**Explanation:**", record["reason"])
    else:
        st.info("No records match your selected filters.")
else:
    st.info(
        "No verification history yet. Verify a claim to create your first record."
    )

# Export verification history
st.divider()
st.subheader("Export Audit Report")

export_history = get_verification_history(limit=50)

if export_history:
    export_df = pd.DataFrame(export_history)

    csv_data = export_df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Download Audit Report (CSV)",
        data=csv_data,
        file_name="claimguard_audit_report.csv",
        mime="text/csv",
    )
else:
    st.info("No verification records available to export.")