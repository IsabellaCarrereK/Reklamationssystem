from datetime import date

import streamlit as st
from database import get_receipt_items

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
        st.warning("Ange ett kvittonummer för att söka.")
    else:
        st.session_state.searched_receipt_id = receipt_id
        st.session_state.receipt_items = get_receipt_items(receipt_id)
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

        if st.button("Skapa reklamationsärende"):
            selected_item = items_by_id[selected_item_id]
            st.info(
                "Ärende kan skapas för: "
                f"{selected_item['product_name']} "
                f"({selected_item['brand'] or 'Okänt varumärke'})."
            )