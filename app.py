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

with st.form("receipt_search"):
    receipt_id = st.text_input("Kvittonummer", placeholder="Exempel: KV-1001")
    search_clicked = st.form_submit_button("Sök kvitto")

if search_clicked:
    receipt_id = receipt_id.strip()

    if not receipt_id:
        st.warning("Ange ett kvittonummer för att söka.")
    else:
        items = get_receipt_items(receipt_id)

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