"""Seed script to populate Firestore database with Indian stocks data."""
import datetime
import google.auth
from google.cloud import firestore

# CRITICAL: Hardcode GCP Project ID as a string.
# On Agent Platform, google.auth.default() or GOOGLE_CLOUD_PROJECT returns the project number.
PROJECT_ID = "qwiklabs-gcp-01-37b29569bd39"
COLLECTION_NAME = "indian_stocks"

INITIAL_STOCKS = [
    {
        "ticker": "RELIANCE",
        "company_name": "Reliance Industries Ltd",
        "sector": "Energy & Conglomerate",
        "current_price": 2950.50,
        "pe_ratio": 28.4,
        "market_cap_cr": 1995000.0,
        "recommendation": "BUY",
        "notes": "Strong retail and telecom growth, expanding green energy initiatives."
    },
    {
        "ticker": "TCS",
        "company_name": "Tata Consultancy Services Ltd",
        "sector": "IT Services & Consulting",
        "current_price": 4120.00,
        "pe_ratio": 31.2,
        "market_cap_cr": 1490000.0,
        "recommendation": "BUY",
        "notes": "Market leader in IT exports with robust order book and dividend history."
    },
    {
        "ticker": "INFY",
        "company_name": "Infosys Ltd",
        "sector": "IT Services & Consulting",
        "current_price": 1850.75,
        "pe_ratio": 26.8,
        "market_cap_cr": 768000.0,
        "recommendation": "HOLD",
        "notes": "Steady digital transformation demand; monitoring attrition and margin recovery."
    },
    {
        "ticker": "HDFCBANK",
        "company_name": "HDFC Bank Ltd",
        "sector": "Banking & Financial Services",
        "current_price": 1640.20,
        "pe_ratio": 18.5,
        "market_cap_cr": 1250000.0,
        "recommendation": "BUY",
        "notes": "India's largest private bank, post-merger integration progressing well."
    },
    {
        "ticker": "TATAMOTORS",
        "company_name": "Tata Motors Ltd",
        "sector": "Automotive",
        "current_price": 975.00,
        "pe_ratio": 11.2,
        "market_cap_cr": 358000.0,
        "recommendation": "BUY",
        "notes": "Leading EV manufacturer in India; strong performance from JLR division."
    }
]

def seed_database():
    print(f"Connecting to Firestore using project ID: '{PROJECT_ID}'...")
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/datastore"]
    )
    db = firestore.Client(project=PROJECT_ID, credentials=creds)
    collection_ref = db.collection(COLLECTION_NAME)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for item in INITIAL_STOCKS:
        doc_id = item["ticker"]
        item["last_updated"] = now_iso
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"  ✓ Seeded document '{doc_id}' ({item['company_name']})")

    print(f"\nSuccessfully seeded {len(INITIAL_STOCKS)} stocks to collection '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    seed_database()
