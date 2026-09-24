"""Seed script to populate Firestore database with comprehensive Indian stocks data."""
import datetime
import google.auth
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-37b29569bd39"
COLLECTION_NAME = "indian_stocks"

INITIAL_STOCKS = [
    {
        "ticker": "RELIANCE",
        "company_name": "Reliance Industries Ltd",
        "sector": "Energy & Conglomerate",
        "current_price": 2980.50,
        "pe_ratio": 28.4,
        "market_cap_cr": 1995000.0,
        "recommendation": "BUY",
        "notes": "Strong retail and telecom growth, expanding green energy initiatives."
    },
    {
        "ticker": "TCS",
        "company_name": "Tata Consultancy Services Ltd",
        "sector": "IT Services & Consulting",
        "current_price": 4210.00,
        "pe_ratio": 31.2,
        "market_cap_cr": 1490000.0,
        "recommendation": "BUY",
        "notes": "Market leader in IT exports with robust order book and dividend history."
    },
    {
        "ticker": "INFY",
        "company_name": "Infosys Ltd",
        "sector": "IT Services & Consulting",
        "current_price": 1895.20,
        "pe_ratio": 26.8,
        "market_cap_cr": 768000.0,
        "recommendation": "HOLD",
        "notes": "Steady digital transformation demand; monitoring attrition and margin recovery."
    },
    {
        "ticker": "HDFCBANK",
        "company_name": "HDFC Bank Ltd",
        "sector": "Banking & Financial Services",
        "current_price": 1642.00,
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
    },
    {
        "ticker": "ICICIBANK",
        "company_name": "ICICI Bank Ltd",
        "sector": "Banking & Financial Services",
        "current_price": 1215.40,
        "pe_ratio": 17.8,
        "market_cap_cr": 855000.0,
        "recommendation": "STRONG BUY",
        "notes": "Consistently industry-leading NIMs, asset quality, and retail credit expansion."
    },
    {
        "ticker": "SBIN",
        "company_name": "State Bank of India",
        "sector": "Banking & Financial Services",
        "current_price": 820.50,
        "pe_ratio": 10.4,
        "market_cap_cr": 732000.0,
        "recommendation": "BUY",
        "notes": "India's largest public sector bank with robust deposit base and low credit cost."
    },
    {
        "ticker": "BHARTIARTL",
        "company_name": "Bharti Airtel Ltd",
        "sector": "Telecommunications",
        "current_price": 1580.00,
        "pe_ratio": 45.2,
        "market_cap_cr": 920000.0,
        "recommendation": "BUY",
        "notes": "Strong ARPU growth, expanding 5G network coverage and enterprise cloud services."
    },
    {
        "ticker": "ITC",
        "company_name": "ITC Ltd",
        "sector": "FMCG & Conglomerate",
        "current_price": 492.30,
        "pe_ratio": 29.1,
        "market_cap_cr": 614000.0,
        "recommendation": "BUY",
        "notes": "High dividend yield, steady FMCG margin expansion, and paperboards recovery."
    },
    {
        "ticker": "LT",
        "company_name": "Larsen & Toubro Ltd",
        "sector": "Infrastructure & Engineering",
        "current_price": 3650.00,
        "pe_ratio": 33.6,
        "market_cap_cr": 501000.0,
        "recommendation": "BUY",
        "notes": "Record order backlog driven by domestic infra spending and Middle East expansion."
    },
    {
        "ticker": "BAJFINANCE",
        "company_name": "Bajaj Finance Ltd",
        "sector": "Financial Services & NBFC",
        "current_price": 7150.00,
        "pe_ratio": 30.5,
        "market_cap_cr": 442000.0,
        "recommendation": "BUY",
        "notes": "Dominant retail lending franchise with rapid digital app ecosystem growth."
    },
    {
        "ticker": "MARUTI",
        "company_name": "Maruti Suzuki India Ltd",
        "sector": "Automotive",
        "current_price": 12450.00,
        "pe_ratio": 27.8,
        "market_cap_cr": 391000.0,
        "recommendation": "HOLD",
        "notes": "Market leader in passenger vehicles; expanding SUV portfolio and hybrid lineup."
    },
    {
        "ticker": "SUNPHARMA",
        "company_name": "Sun Pharmaceutical Industries Ltd",
        "sector": "Pharmaceuticals & Healthcare",
        "current_price": 1820.00,
        "pe_ratio": 36.4,
        "market_cap_cr": 436000.0,
        "recommendation": "BUY",
        "notes": "Global specialty pharma franchise with expanding US and emerging markets pipeline."
    },
    {
        "ticker": "ASIANPAINT",
        "company_name": "Asian Paints Ltd",
        "sector": "Consumer Goods & Paints",
        "current_price": 3110.00,
        "pe_ratio": 52.1,
        "market_cap_cr": 298000.0,
        "recommendation": "HOLD",
        "notes": "Market leader in decorative paints with strong brand equity and distribution network."
    },
    {
        "ticker": "ALLIED",
        "company_name": "Allied Blenders & Distillers Ltd",
        "sector": "Consumer Spirits & Alcobev",
        "current_price": 342.10,
        "pe_ratio": 42.0,
        "market_cap_cr": 9560.0,
        "recommendation": "BUY",
        "notes": "Iconic Officer's Choice maker; premiumization strategy boosting gross margins."
    },
    {
        "ticker": "BRAINBEES",
        "company_name": "Brainbees Solutions Ltd (FirstCry)",
        "sector": "Retail & E-Commerce",
        "current_price": 635.00,
        "pe_ratio": 65.0,
        "market_cap_cr": 33000.0,
        "recommendation": "BUY",
        "notes": "Dominant omnichannel mother & baby care brand expanding across India and UAE."
    },
    {
        "ticker": "HAL",
        "company_name": "Hindustan Aeronautics Ltd",
        "sector": "Defence & Aerospace",
        "current_price": 4650.00,
        "pe_ratio": 38.2,
        "market_cap_cr": 311000.0,
        "recommendation": "BUY",
        "notes": "Monopoly defence aircraft manufacturer with multi-year order book from Indian Armed Forces."
    },
    {
        "ticker": "NTPC",
        "company_name": "NTPC Ltd",
        "sector": "Utilities & Power",
        "current_price": 415.00,
        "pe_ratio": 19.4,
        "market_cap_cr": 402000.0,
        "recommendation": "BUY",
        "notes": "India's largest power producer expanding aggressively into solar and green hydrogen."
    },
    {
        "ticker": "TITAN",
        "company_name": "Titan Company Ltd",
        "sector": "Consumer Durables & Jewelry",
        "current_price": 3680.00,
        "pe_ratio": 82.5,
        "market_cap_cr": 326000.0,
        "recommendation": "BUY",
        "notes": "Tata Group flagship in jewelry (Tanishq) and eyewear with compounding store growth."
    },
    {
        "ticker": "LTIM",
        "company_name": "LTIMindtree Ltd",
        "sector": "IT Services & Consulting",
        "current_price": 6120.00,
        "pe_ratio": 34.0,
        "market_cap_cr": 181000.0,
        "recommendation": "BUY",
        "notes": "Tier-1 IT provider specializing in cloud migration, AI implementations, and data engineering."
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
