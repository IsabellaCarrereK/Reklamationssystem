from datetime import date
import sqlite3

import streamlit as st
from database import (
    create_claim,
    get_all_claims,
    get_existing_claim_for_item,
    get_receipt_items,
    update_claim_assessment,
)

st.set_page_config(
    page_title="Reklamationssystem",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Reklamationssystem")
st.write("Digital hantering av reklamationsärenden")

st.divider()

st.subheader("Välkommen!")
st.write("Här kommer vi att kunna registrera och hantera reklamationer.")

st.info("🚧 Applikationen är under utveckling.")

st.divider()
st.subheader("Sök kvitto")

st.session_state.setdefault("searched_receipt_id", None)
st.session_state.setdefault("receipt_items", [])
st.session_state.setdefault("selected_receipt_item_id", None)
st.session_state.setdefault("claim_form_open", False)
st.session_state.setdefault("claim_form_item_id", None)
st.session_state.setdefault("created_claims", {})

with st.form("receipt_search"):
    receipt_id = st.text_input(
        "Kvittonummer",
        placeholder="Exempel: KV-1001",
        key="receipt_search_input",
    )
    search_clicked = st.form_submit_button("Sök kvitto")

if search_clicked:
    receipt_id = receipt_id.strip()

    if not receipt_id:
        st.session_state.searched_receipt_id = None
        st.session_state.receipt_items = []
        st.session_state.selected_receipt_item_id = None
        st.session_state.claim_form_open = False
        st.session_state.claim_form_item_id = None
        st.warning("Ange ett kvittonummer för att söka.")
    else:
        st.session_state.searched_receipt_id = receipt_id
        st.session_state.receipt_items = get_receipt_items(receipt_id)
        st.session_state.claim_form_open = False
        st.session_state.claim_form_item_id = None
        st.session_state.selected_receipt_item_id = (
            st.session_state.receipt_items[0]["item_id"]
            if st.session_state.receipt_items
            else None
        )

if st.session_state.searched_receipt_id:
    items = st.session_state.receipt_items

    if not items:
        st.error("Inget kvitto hittades med det kvittonumret.")
    else:
        purchase_date = date.fromisoformat(items[0]["purchase_date"])
        days_since_purchase = (date.today() - purchase_date).days

        st.subheader(f"Kvitto {items[0]['receipt_id']}")
        receipt_details = st.columns(2)
        receipt_details[0].metric("Köpdatum", purchase_date.isoformat())
        receipt_details[1].metric("Dagar sedan köpet", days_since_purchase)

        st.subheader("Artiklar")
        st.table([
            {
                "Produktnamn": item["product_name"],
                "Varumärke": item["brand"],
                "Pris": f"{item['purchase_price']:.2f} kr",
                "Antal": item["quantity"],
            }
            for item in items
        ])

        items_by_id = {item["item_id"]: item for item in items}
        selected_item_id = st.radio(
            "Välj kvittorad att reklamera",
            options=list(items_by_id),
            format_func=lambda item_id: (
                f"Rad {item_id}: {items_by_id[item_id]['product_name']} - "
                f"{items_by_id[item_id]['brand'] or 'Okänt varumärke'}"
            ),
            key="selected_receipt_item_id",
        )

        if (
            st.session_state.claim_form_open
            and st.session_state.claim_form_item_id != selected_item_id
        ):
            st.session_state.claim_form_open = False
            st.session_state.claim_form_item_id = None

        selected_item = items_by_id[selected_item_id]
        existing_claim = get_existing_claim_for_item(selected_item_id)
        existing_claim_id = st.session_state.created_claims.get(selected_item_id)
        if existing_claim is None and existing_claim_id is not None:
            st.session_state.created_claims.pop(selected_item_id, None)
            existing_claim_id = None

        if existing_claim is not None:
            if st.session_state.claim_form_item_id == selected_item_id:
                st.session_state.claim_form_open = False
                st.session_state.claim_form_item_id = None
            decision_value = existing_claim.get("decision")
            if decision_value is None or (
                isinstance(decision_value, str) and not decision_value.strip()
            ):
                decision_value = "Ej bedömd"
            st.info("**Reklamation redan registrerad**")
            st.write(
                "**Ärendenummer:**",
                existing_claim.get("claim_id", "Ej angivet"),
            )
            st.write(
                "**Status:**",
                existing_claim.get("status") or "Ej angivet",
            )
            st.write("**Beslut:**", decision_value)
        elif existing_claim_id is not None:
            st.success(
                f"Reklamationsärende {existing_claim_id} är registrerat "
                "med status Registrerad."
            )
        elif not st.session_state.claim_form_open:
            if st.button("Skapa reklamationsärende"):
                st.session_state.claim_form_open = True
                st.session_state.claim_form_item_id = selected_item_id

        if (
            st.session_state.claim_form_open
            and st.session_state.claim_form_item_id == selected_item_id
            and existing_claim_id is None
            and existing_claim is None
        ):
            st.write(
                f"Reklamation för **{selected_item['product_name']}** "
                f"på kvitto **{st.session_state.searched_receipt_id}**."
            )

            with st.form(f"claim_form_{selected_item_id}"):
                customer_name = st.text_input(
                    "Kundens namn", key=f"claim_customer_name_{selected_item_id}"
                )
                customer_phone = st.text_input(
                    "Kundens telefonnummer",
                    key=f"claim_customer_phone_{selected_item_id}",
                )
                reason = st.selectbox(
                    "Reklamationsorsak",
                    ["", "Trasig vara", "Kvalitetsfel", "Saknad del", "Annat"],
                    format_func=lambda value: value or "Välj orsak",
                    key=f"claim_reason_{selected_item_id}",
                )
                description = st.text_area(
                    "Felbeskrivning", key=f"claim_description_{selected_item_id}"
                )
                received_by = st.text_input(
                    "Mottagande personal",
                    key=f"claim_received_by_{selected_item_id}",
                )
                claim_submitted = st.form_submit_button("Registrera reklamation")

            if claim_submitted:
                required_values = (
                    customer_name,
                    customer_phone,
                    description,
                    received_by,
                )
                if any(not value.strip() for value in required_values):
                    st.error("Fyll i alla obligatoriska textfält.")
                elif not reason:
                    st.error("Välj en reklamationsorsak.")
                else:
                    claim_id = create_claim(
                        selected_item_id,
                        customer_name.strip(),
                        customer_phone.strip(),
                        reason,
                        description.strip(),
                        received_by.strip(),
                    )
                    st.session_state.created_claims[selected_item_id] = claim_id
                    st.session_state.claim_form_open = False
                    st.session_state.claim_form_item_id = None
                    st.success(
                        f"Reklamationsärende {claim_id} är registrerat "
                        "med status Registrerad."
                    )

st.divider()
st.subheader("Registrerade reklamationer")

claims = get_all_claims()
if not claims:
    st.info("Det finns inga registrerade reklamationer ännu.")
else:
    st.dataframe(
        [
            {
                "Ärendenummer": claim["claim_id"],
                "Kund": claim["customer_name"],
                "Produkt": claim["product_name"],
                "Kvitto": claim["receipt_id"],
                "Status": claim["status"],
                "Registrerad": claim["created_at"],
            }
            for claim in claims
        ],
        hide_index=True,
        use_container_width=True,
    )

    claim_by_id = {claim["claim_id"]: claim for claim in claims}
    st.subheader("Ärendedetaljer")
    selected_claim_id = st.selectbox(
        "Välj reklamationsärende",
        options=list(claim_by_id),
        format_func=lambda claim_id: (
            f"Ärende {claim_id} - "
            f"{claim_by_id[claim_id]['product_name'] or 'Produkt saknas'}"
        ),
        key="selected_claim_details",
    )
    selected_claim = claim_by_id[selected_claim_id]

    def display_claim_value(value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return "Ej angivet"
        return value

    with st.container():
        left_column, right_column = st.columns(2)
        with left_column:
            st.write("**Ärendenummer:**", display_claim_value(selected_claim["claim_id"]))
            st.write("**Kundnamn:**", display_claim_value(selected_claim["customer_name"]))
            st.write("**Telefonnummer:**", display_claim_value(selected_claim["customer_phone"]))
            st.write("**Produkt:**", display_claim_value(selected_claim["product_name"]))
            st.write("**Kvittonummer:**", display_claim_value(selected_claim["receipt_id"]))
        with right_column:
            st.write("**Reklamationsorsak:**", display_claim_value(selected_claim["reason"]))
            st.write("**Felbeskrivning:**", display_claim_value(selected_claim["description"]))
            st.write("**Status:**", display_claim_value(selected_claim["status"]))
            st.write(
                "**Mottagande personal:**",
                display_claim_value(selected_claim["received_by"]),
            )
            st.write("**Registreringsdatum:**", display_claim_value(selected_claim["created_at"]))

    st.subheader("Registrerad bedömning")
    decision_value = selected_claim.get("decision")
    has_decision = decision_value is not None and not (
        isinstance(decision_value, str) and not decision_value.strip()
    )
    if not has_decision:
        st.info("Ingen bedömning har registrerats ännu.")
    else:
        resolution_value = selected_claim.get("resolution")
        if resolution_value is None or (
            isinstance(resolution_value, str) and not resolution_value.strip()
        ):
            resolution_value = "Ingen åtgärd"
        st.write("**Beslut:**", display_claim_value(decision_value))
        st.write("**Åtgärd:**", display_claim_value(resolution_value))
        st.write(
            "**Bedömd av (personal-ID):**",
            display_claim_value(selected_claim.get("assessed_by_staff_id")),
        )
        st.write(
            "**Bedömningsdatum:**",
            display_claim_value(selected_claim.get("assessed_at")),
        )

    if has_decision:
        st.info("Det här ärendet är redan bedömt. Beslutet kan inte ändras här.")
    else:
        st.subheader("Bedöm reklamation")
        with st.form(f"assessment_form_{selected_claim['claim_id']}"):
            decision = st.selectbox(
                "Beslut",
                options=["Godkänd", "Nekad"],
                index=None,
                placeholder="Välj beslut",
                key=f"assessment_decision_{selected_claim['claim_id']}",
            )
            resolution = st.selectbox(
                "Åtgärd (endast vid godkännande)",
                options=["Reparation", "Återbetalning", "Ny vara"],
                index=None,
                placeholder="Välj åtgärd",
                key=f"assessment_resolution_{selected_claim['claim_id']}",
            )
            assessed_by_staff_id = st.text_input(
                "Personal-ID",
                key=f"assessment_staff_id_{selected_claim['claim_id']}",
            )
            assessment_submitted = st.form_submit_button("Spara bedömning")

        if assessment_submitted:
            if not assessed_by_staff_id.strip():
                st.error("Ange personal-ID innan bedömningen sparas.")
            elif decision is None:
                st.error("Välj om reklamationen ska godkännas eller nekas.")
            elif decision == "Godkänd" and resolution is None:
                st.error("Välj en åtgärd för den godkända reklamationen.")
            else:
                try:
                    update_claim_assessment(
                        selected_claim["claim_id"],
                        decision,
                        resolution if decision == "Godkänd" else None,
                        assessed_by_staff_id.strip(),
                    )
                except sqlite3.Error:
                    st.error("Bedömningen kunde inte sparas på grund av ett databasfel.")
                else:
                    st.success(
                        f"Bedömningen för ärende {selected_claim['claim_id']} har sparats."
                    )