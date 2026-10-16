from html import escape


def _escaped_claim_values(claim):
    values = {}
    for key in (
        "claim_id",
        "customer_name",
        "customer_phone",
        "product_name",
        "receipt_id",
        "reason",
        "description",
        "created_at",
        "received_by",
    ):
        value = claim.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            value = "Ej angivet"
        values[key] = escape(str(value), quote=True)
    return values


def _document_page(title, content):
    return f"""<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title, quote=True)}</title>
    <style>
        @page {{ size: A4; margin: 20mm; }}
        body {{
            background: #fff;
            color: #000;
            font-family: Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.5;
            margin: 0 auto;
            max-width: 170mm;
        }}
        h1 {{ font-size: 20pt; }}
        dt {{ font-weight: bold; margin-top: 0.75em; }}
        dd {{ margin-left: 0; white-space: pre-wrap; }}
        @media screen {{
            body {{ padding: 20mm; }}
        }}
    </style>
</head>
<body>
{content}
</body>
</html>
"""


def generate_customer_receipt_html(claim):
    values = _escaped_claim_values(claim)
    content = f"""<h1>Inlämningsbevis för reklamation</h1>
<dl>
    <dt>Ärendenummer</dt><dd>{values["claim_id"]}</dd>
    <dt>Kundnamn</dt><dd>{values["customer_name"]}</dd>
    <dt>Produkt</dt><dd>{values["product_name"]}</dd>
    <dt>Kvittonummer</dt><dd>{values["receipt_id"]}</dd>
    <dt>Mottagningsdatum</dt><dd>{values["created_at"]}</dd>
</dl>
<p>Vi har tagit emot din reklamation för bedömning. Mottagandet innebär
inte att reklamationen automatiskt har godkänts.</p>
"""
    return _document_page("Inlämningsbevis för reklamation", content)


def generate_store_claim_html(claim):
    values = _escaped_claim_values(claim)
    content = f"""<h1>Reklamationsunderlag</h1>
<dl>
    <dt>Ärendenummer</dt><dd>{values["claim_id"]}</dd>
    <dt>Produkt</dt><dd>{values["product_name"]}</dd>
    <dt>Kundnamn</dt><dd>{values["customer_name"]}</dd>
    <dt>Telefonnummer</dt><dd>{values["customer_phone"]}</dd>
    <dt>Kvittonummer</dt><dd>{values["receipt_id"]}</dd>
    <dt>Reklamationsorsak</dt><dd>{values["reason"]}</dd>
    <dt>Felbeskrivning</dt><dd>{values["description"]}</dd>
    <dt>Mottagningsdatum</dt><dd>{values["created_at"]}</dd>
    <dt>Mottagande personal</dt><dd>{values["received_by"]}</dd>
</dl>
"""
    return _document_page("Reklamationsunderlag", content)
