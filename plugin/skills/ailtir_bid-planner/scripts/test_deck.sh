#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cat > /tmp/deck.json <<'JSON'
{"project":"Athenry NRR","client":"Galway CC","value":"€2.0M","sector":"Civils","returnDate":"2026-02-28",
"overview":["Road widening","Bridge works"],"packStatus":{"received":12,"missing":2,"gaps":3},
"missingDocs":[{"doc":"Geotech report","impact":"Pricing blind"}],"priceOnly":true,
"requirements":[{"ref":"WP-1","text":"PSCS statement","owner":"Director"}],
"programme":[{"date":"2026-02-07","label":"Query deadline"}],
"packages":[{"name":"Groundworks"},{"name":"Concrete"}],
"risks":[{"title":"20-day time bar","owner":"Commercial"}],
"actions":[{"when":"TODAY","what":"Issue subbie enquiries","who":"Estimator"}]}
JSON
node create_bid_deck.js --config /tmp/deck.json --output /tmp/deck.pptx
test -s /tmp/deck.pptx
echo "DECK OK"
