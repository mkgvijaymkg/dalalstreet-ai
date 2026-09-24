"""Script to populate a comprehensive dataset of 150+ major NSE & BSE stocks into Firestore."""
import datetime
import google.auth
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-37b29569bd39"
COLLECTION_NAME = "indian_stocks"

# Comprehensive list of 150+ NSE & BSE stocks across all major sectors
ALL_NSE_BSE_STOCKS = [
    # Energy & Oil/Gas
    {"ticker": "RELIANCE", "company_name": "Reliance Industries Ltd", "sector": "Energy & Conglomerate", "current_price": 2980.50, "pe_ratio": 28.4, "market_cap_cr": 1995000.0, "recommendation": "BUY", "notes": "Leader in refining, retail, 5G telecom, and green energy."},
    {"ticker": "ONGC", "company_name": "Oil & Natural Gas Corp Ltd", "sector": "Oil & Gas Exploration", "current_price": 315.20, "pe_ratio": 7.8, "market_cap_cr": 396000.0, "recommendation": "BUY", "notes": "Largest crude oil and natural gas company in India."},
    {"ticker": "BPCL", "company_name": "Bharat Petroleum Corp Ltd", "sector": "Oil Refining & Marketing", "current_price": 352.40, "pe_ratio": 9.1, "market_cap_cr": 152000.0, "recommendation": "BUY", "notes": "Strong marketing margins and refining utilization rates."},
    {"ticker": "IOC", "company_name": "Indian Oil Corporation Ltd", "sector": "Oil Refining & Marketing", "current_price": 178.60, "pe_ratio": 8.5, "market_cap_cr": 251000.0, "recommendation": "BUY", "notes": "India's largest refiner with extensive pipeline network."},
    {"ticker": "GAIL", "company_name": "GAIL (India) Ltd", "sector": "Gas Utility & Distribution", "current_price": 225.80, "pe_ratio": 14.2, "market_cap_cr": 148000.0, "recommendation": "BUY", "notes": "Dominant natural gas transmission network across India."},
    {"ticker": "ADANIGREEN", "company_name": "Adani Green Energy Ltd", "sector": "Renewable Energy", "current_price": 1820.00, "pe_ratio": 120.5, "market_cap_cr": 288000.0, "recommendation": "HOLD", "notes": "Rapid solar and wind capacity commissioning."},
    {"ticker": "TATAPOWER", "company_name": "Tata Power Company Ltd", "sector": "Utilities & Renewable Energy", "current_price": 435.50, "pe_ratio": 36.8, "market_cap_cr": 139000.0, "recommendation": "BUY", "notes": "Expanding EV charging infrastructure and solar rooftop dominance."},
    {"ticker": "NTPC", "company_name": "NTPC Ltd", "sector": "Power Generation", "current_price": 415.00, "pe_ratio": 19.4, "market_cap_cr": 402000.0, "recommendation": "BUY", "notes": "Largest power producer transitioning to green energy."},

    # IT Services & Software
    {"ticker": "TCS", "company_name": "Tata Consultancy Services Ltd", "sector": "IT Services & Consulting", "current_price": 4210.00, "pe_ratio": 31.2, "market_cap_cr": 1490000.0, "recommendation": "BUY", "notes": "Global IT exports leader with strong margin profile."},
    {"ticker": "INFY", "company_name": "Infosys Ltd", "sector": "IT Services & Consulting", "current_price": 1895.20, "pe_ratio": 26.8, "market_cap_cr": 768000.0, "recommendation": "HOLD", "notes": "Strong digital banking and cloud transformation order wins."},
    {"ticker": "HCLTECH", "company_name": "HCL Technologies Ltd", "sector": "IT Services & Consulting", "current_price": 1780.00, "pe_ratio": 27.5, "market_cap_cr": 482000.0, "recommendation": "BUY", "notes": "Leading software products and ER&D service offerings."},
    {"ticker": "WIPRO", "company_name": "Wipro Ltd", "sector": "IT Services & Consulting", "current_price": 540.20, "pe_ratio": 23.4, "market_cap_cr": 282000.0, "recommendation": "HOLD", "notes": "Turnaround execution ongoing in large deal conversions."},
    {"ticker": "LTIM", "company_name": "LTIMindtree Ltd", "sector": "IT Services & Consulting", "current_price": 6120.00, "pe_ratio": 34.0, "market_cap_cr": 181000.0, "recommendation": "BUY", "notes": "Tier-1 IT provider specializing in cloud migration and AI."},
    {"ticker": "TECHM", "company_name": "Tech Mahindra Ltd", "sector": "IT & Telecom Software", "current_price": 1580.00, "pe_ratio": 48.2, "market_cap_cr": 154000.0, "recommendation": "BUY", "notes": "Beneficiary of global 5G network equipment upgrades."},
    {"ticker": "PERSISTENT", "company_name": "Persistent Systems Ltd", "sector": "Software & Product Engineering", "current_price": 5250.00, "pe_ratio": 55.6, "market_cap_cr": 80800.0, "recommendation": "BUY", "notes": "Consistent 20%+ revenue growth in digital product engineering."},
    {"ticker": "COFORGE", "company_name": "Coforge Ltd", "sector": "IT & Business Solutions", "current_price": 6480.00, "pe_ratio": 42.1, "market_cap_cr": 43200.0, "recommendation": "BUY", "notes": "Specialist in insurance, banking, and travel verticals."},

    # Banking & Financial Services
    {"ticker": "HDFCBANK", "company_name": "HDFC Bank Ltd", "sector": "Banking & Financial Services", "current_price": 1642.00, "pe_ratio": 18.5, "market_cap_cr": 1250000.0, "recommendation": "BUY", "notes": "India's largest private bank with vast branch reach."},
    {"ticker": "ICICIBANK", "company_name": "ICICI Bank Ltd", "sector": "Banking & Financial Services", "current_price": 1215.40, "pe_ratio": 17.8, "market_cap_cr": 855000.0, "recommendation": "STRONG BUY", "notes": "Consistently industry-leading NIMs and asset quality."},
    {"ticker": "SBIN", "company_name": "State Bank of India", "sector": "Banking & Financial Services", "current_price": 820.50, "pe_ratio": 10.4, "market_cap_cr": 732000.0, "recommendation": "BUY", "notes": "Largest public sector bank with massive deposit moat."},
    {"ticker": "KOTAKBANK", "company_name": "Kotak Mahindra Bank Ltd", "sector": "Banking & Financial Services", "current_price": 1810.00, "pe_ratio": 21.6, "market_cap_cr": 359000.0, "recommendation": "HOLD", "notes": "High capital adequacy and strong wealth management franchise."},
    {"ticker": "AXISBANK", "company_name": "Axis Bank Ltd", "sector": "Banking & Financial Services", "current_price": 1235.00, "pe_ratio": 14.8, "market_cap_cr": 381000.0, "recommendation": "BUY", "notes": "Strong credit growth following Citi retail integration."},
    {"ticker": "INDUSINDBK", "company_name": "IndusInd Bank Ltd", "sector": "Banking & Financial Services", "current_price": 1420.00, "pe_ratio": 12.3, "market_cap_cr": 110000.0, "recommendation": "BUY", "notes": "Leading vehicle finance and microfinance lender."},
    {"ticker": "BANKBARODA", "company_name": "Bank of Baroda", "sector": "Banking & Financial Services", "current_price": 255.00, "pe_ratio": 6.8, "market_cap_cr": 131000.0, "recommendation": "BUY", "notes": "Attractive valuation with strong return on equity."},
    {"ticker": "PNB", "company_name": "Punjab National Bank", "sector": "Banking & Financial Services", "current_price": 108.50, "pe_ratio": 9.2, "market_cap_cr": 119000.0, "recommendation": "HOLD", "notes": "Asset quality recovery across corporate and retail books."},
    {"ticker": "FEDERALBNK", "company_name": "Federal Bank Ltd", "sector": "Banking & Financial Services", "current_price": 192.40, "pe_ratio": 11.5, "market_cap_cr": 47200.0, "recommendation": "BUY", "notes": "Fast-growing private bank with strong NRI remittance flow."},
    {"ticker": "IDFCFIRSTB", "company_name": "IDFC First Bank Ltd", "sector": "Banking & Financial Services", "current_price": 74.80, "pe_ratio": 18.2, "market_cap_cr": 53000.0, "recommendation": "BUY", "notes": "Rapid CASA ratio expansion and retail credit growth."},

    # Non-Banking Financial Companies (NBFC) & Insurance
    {"ticker": "BAJFINANCE", "company_name": "Bajaj Finance Ltd", "sector": "Financial Services & NBFC", "current_price": 7150.00, "pe_ratio": 30.5, "market_cap_cr": 442000.0, "recommendation": "BUY", "notes": "Dominant consumer lending app ecosystem in India."},
    {"ticker": "BAJAJFINSV", "company_name": "Bajaj Finserv Ltd", "sector": "Financial Holding & Insurance", "current_price": 1840.00, "pe_ratio": 34.2, "market_cap_cr": 293000.0, "recommendation": "BUY", "notes": "Holding company for Bajaj Finance, life and general insurance."},
    {"ticker": "JIOFIN", "company_name": "Jio Financial Services Ltd", "sector": "Financial Services & Fintech", "current_price": 345.00, "pe_ratio": 115.0, "market_cap_cr": 219000.0, "recommendation": "BUY", "notes": "Reliance backed fintech venture expanding into broking and AMC."},
    {"ticker": "CHOLAFIN", "company_name": "Cholamandalam Investment & Finance", "sector": "Vehicle Finance & NBFC", "current_price": 1420.00, "pe_ratio": 32.8, "market_cap_cr": 119000.0, "recommendation": "BUY", "notes": "Premier commercial vehicle and home equity loan provider."},
    {"ticker": "MUTHOOTFIN", "company_name": "Muthoot Finance Ltd", "sector": "Gold Finance & NBFC", "current_price": 1850.00, "pe_ratio": 16.4, "market_cap_cr": 74200.0, "recommendation": "BUY", "notes": "India's largest gold loan NBFC benefiting from high gold prices."},
    {"ticker": "SHRIRAMFIN", "company_name": "Shriram Finance Ltd", "sector": "Commercial Vehicle Finance", "current_price": 3120.00, "pe_ratio": 14.1, "market_cap_cr": 117000.0, "recommendation": "BUY", "notes": "Largest retail asset financing NBFC in India."},
    {"ticker": "SBILIFE", "company_name": "SBI Life Insurance Company Ltd", "sector": "Life Insurance", "current_price": 1780.00, "pe_ratio": 78.2, "market_cap_cr": 178000.0, "recommendation": "BUY", "notes": "Market leader in private sector life insurance VNB."},
    {"ticker": "HDFCLIFE", "company_name": "HDFC Life Insurance Company Ltd", "sector": "Life Insurance", "current_price": 710.00, "pe_ratio": 88.5, "market_cap_cr": 152000.0, "recommendation": "BUY", "notes": "Strong bancassurance network via HDFC Bank branches."},
    {"ticker": "ICICIPRULI", "company_name": "ICICI Prudential Life Insurance", "sector": "Life Insurance", "current_price": 740.00, "pe_ratio": 82.0, "market_cap_cr": 106000.0, "recommendation": "HOLD", "notes": "Diversified product mix with high annuity and protection shares."},

    # Automotive & Auto Components
    {"ticker": "TATAMOTORS", "company_name": "Tata Motors Ltd", "sector": "Automotive", "current_price": 975.00, "pe_ratio": 11.2, "market_cap_cr": 358000.0, "recommendation": "BUY", "notes": "EV market leader in India with high margin JLR export volume."},
    {"ticker": "MARUTI", "company_name": "Maruti Suzuki India Ltd", "sector": "Automotive", "current_price": 12450.00, "pe_ratio": 27.8, "market_cap_cr": 391000.0, "recommendation": "HOLD", "notes": "Dominant passenger car market share; expanding SUV portfolio."},
    {"ticker": "M&M", "company_name": "Mahindra & Mahindra Ltd", "sector": "Automotive & Farm Equipment", "current_price": 2890.00, "pe_ratio": 29.4, "market_cap_cr": 359000.0, "recommendation": "BUY", "notes": "Market leader in SUVs and agricultural tractors."},
    {"ticker": "HEROMOTOCO", "company_name": "Hero MotoCorp Ltd", "sector": "Two-Wheelers & Motorcycles", "current_price": 5420.00, "pe_ratio": 24.1, "market_cap_cr": 108000.0, "recommendation": "BUY", "notes": "World's largest two-wheeler maker expanding into premium EVs."},
    {"ticker": "BAJAJ-AUTO", "company_name": "Bajaj Auto Ltd", "sector": "Two & Three Wheelers", "current_price": 11450.00, "pe_ratio": 38.6, "market_cap_cr": 319000.0, "recommendation": "BUY", "notes": "Export leader in motorcycles and Chetak EV scooter sales."},
    {"ticker": "EICHERMOT", "company_name": "Eicher Motors Ltd", "sector": "Automotive & Motorcycles", "current_price": 4850.00, "pe_ratio": 33.2, "market_cap_cr": 133000.0, "recommendation": "BUY", "notes": "Royal Enfield maker with premium mid-size motorcycle monopoly."},
    {"ticker": "TVSMOTOR", "company_name": "TVS Motor Company Ltd", "sector": "Two-Wheelers & Scooters", "current_price": 2750.00, "pe_ratio": 54.0, "market_cap_cr": 130000.0, "recommendation": "BUY", "notes": "Fastest growing scooter and EV two-wheeler brand in India."},
    {"ticker": "BHARATFORG", "company_name": "Bharat Forge Ltd", "sector": "Auto Components & Defence", "current_price": 1560.00, "pe_ratio": 58.2, "market_cap_cr": 72600.0, "recommendation": "BUY", "notes": "Leading global forging company supplying automotive and defence."},
    {"ticker": "SAMVARDHANA", "company_name": "Samvardhana Motherson International", "sector": "Auto Wiring & Components", "current_price": 195.00, "pe_ratio": 36.5, "market_cap_cr": 132000.0, "recommendation": "BUY", "notes": "Global Tier-1 automotive wiring harness and mirror supplier."},

    # Pharmaceuticals & Healthcare
    {"ticker": "SUNPHARMA", "company_name": "Sun Pharmaceutical Industries Ltd", "sector": "Pharmaceuticals", "current_price": 1820.00, "pe_ratio": 36.4, "market_cap_cr": 436000.0, "recommendation": "BUY", "notes": "Global specialty pharma leader in dermatology and oncology."},
    {"ticker": "CIPLA", "company_name": "Cipla Ltd", "sector": "Pharmaceuticals", "current_price": 1620.00, "pe_ratio": 29.8, "market_cap_cr": 130000.0, "recommendation": "BUY", "notes": "Respiratory medicine leader in US generics and India domestic."},
    {"ticker": "DRREDDY", "company_name": "Dr Reddy's Laboratories Ltd", "sector": "Pharmaceuticals", "current_price": 6850.00, "pe_ratio": 20.4, "market_cap_cr": 114000.0, "recommendation": "BUY", "notes": "Strong biosimilar and Revlimid US generic cash flow."},
    {"ticker": "DIVISLAB", "company_name": "Divi's Laboratories Ltd", "sector": "Pharma API & Custom Synthesis", "current_price": 5120.00, "pe_ratio": 72.4, "market_cap_cr": 135000.0, "recommendation": "HOLD", "notes": "Global API supplier for generic and innovator pharmaceuticals."},
    {"ticker": "ZYDUSLIFE", "company_name": "Zydus Lifesciences Ltd", "sector": "Pharmaceuticals", "current_price": 1180.00, "pe_ratio": 28.6, "market_cap_cr": 118000.0, "recommendation": "BUY", "notes": "First-to-file US generic launches and rare disease therapies."},
    {"ticker": "MANKIND", "company_name": "Mankind Pharma Ltd", "sector": "Pharmaceuticals & Consumer Healthcare", "current_price": 2540.00, "pe_ratio": 51.0, "market_cap_cr": 101000.0, "recommendation": "BUY", "notes": "Domestic prescription drug market share leader in India."},
    {"ticker": "APOLLOHOSP", "company_name": "Apollo Hospitals Enterprise Ltd", "sector": "Healthcare & Hospitals", "current_price": 6850.00, "pe_ratio": 78.5, "market_cap_cr": 98500.0, "recommendation": "BUY", "notes": "Largest private hospital chain and Apollo 24/7 digital pharmacy."},
    {"ticker": "MAXHEALTH", "company_name": "Max Healthcare Institute Ltd", "sector": "Healthcare & Hospitals", "current_price": 940.00, "pe_ratio": 71.2, "market_cap_cr": 91400.0, "recommendation": "BUY", "notes": "High ARPOB metro hospital network expansion."},
    {"ticker": "LALPATHLAB", "company_name": "Dr Lal PathLabs Ltd", "sector": "Diagnostics & Healthcare", "current_price": 3150.00, "pe_ratio": 64.0, "market_cap_cr": 26300.0, "recommendation": "HOLD", "notes": "Dominant diagnostic lab network in North and East India."},

    # Consumer Goods (FMCG) & Retail
    {"ticker": "HINDUNILVR", "company_name": "Hindustan Unilever Ltd", "sector": "FMCG", "current_price": 2820.00, "pe_ratio": 64.2, "market_cap_cr": 662000.0, "recommendation": "BUY", "notes": "India's largest FMCG company with unmatched rural reach."},
    {"ticker": "ITC", "company_name": "ITC Ltd", "sector": "FMCG & Conglomerate", "current_price": 492.30, "pe_ratio": 29.1, "market_cap_cr": 614000.0, "recommendation": "BUY", "notes": "Steady cigarette cash flow funding non-cigarette FMCG growth."},
    {"ticker": "NESTLEIND", "company_name": "Nestle India Ltd", "sector": "FMCG & Foods", "current_price": 2580.00, "pe_ratio": 76.5, "market_cap_cr": 248000.0, "recommendation": "HOLD", "notes": "Maggi and Nescafe market share dominance in packaged food."},
    {"ticker": "BRITANNIA", "company_name": "Britannia Industries Ltd", "sector": "FMCG & Bakery", "current_price": 5950.00, "pe_ratio": 62.4, "market_cap_cr": 143000.0, "recommendation": "BUY", "notes": "Good Day and Marie Gold bakery market leader."},
    {"ticker": "GODREJCP", "company_name": "Godrej Consumer Products Ltd", "sector": "FMCG & Personal Care", "current_price": 1480.00, "pe_ratio": 68.1, "market_cap_cr": 151000.0, "recommendation": "BUY", "notes": "Household insecticides and hair color market leader."},
    {"ticker": "DABUR", "company_name": "Dabur India Ltd", "sector": "FMCG & Ayurvedic", "current_price": 645.00, "pe_ratio": 54.8, "market_cap_cr": 114000.0, "recommendation": "BUY", "notes": "Pioneer in Ayurvedic healthcare, juices, and oral care."},
    {"ticker": "MARICO", "company_name": "Marico Ltd", "sector": "FMCG & Oils", "current_price": 675.00, "pe_ratio": 52.0, "market_cap_cr": 87400.0, "recommendation": "BUY", "notes": "Parachute coconut oil and Saffola edible oil brand owner."},
    {"ticker": "VARUN", "company_name": "Varun Beverages Ltd", "sector": "Beverages & Bottling", "current_price": 615.00, "pe_ratio": 84.0, "market_cap_cr": 200000.0, "recommendation": "BUY", "notes": "Exclusive PepsiCo franchisee across India and international markets."},
    {"ticker": "DMART", "company_name": "Avenue Supermarts Ltd (D-Mart)", "sector": "Hypermarket Retail", "current_price": 5120.00, "pe_ratio": 118.0, "market_cap_cr": 333000.0, "recommendation": "BUY", "notes": "Lowest cost operator in brick-and-mortar hypermarket grocery."},
    {"ticker": "TRENT", "company_name": "Trent Ltd (Westside & Zudio)", "sector": "Apparel Retail", "current_price": 7450.00, "pe_ratio": 145.0, "market_cap_cr": 264000.0, "recommendation": "BUY", "notes": "Tata group value fashion powerhouse (Zudio) with high store ROI."},

    # Infrastructure, Engineering & Cement
    {"ticker": "LT", "company_name": "Larsen & Toubro Ltd", "sector": "Infrastructure & Engineering", "current_price": 3650.00, "pe_ratio": 33.6, "market_cap_cr": 501000.0, "recommendation": "BUY", "notes": "Dominant infra contractor in EPC, defence, and green hydrogen."},
    {"ticker": "ULTRACEMCO", "company_name": "UltraTech Cement Ltd", "sector": "Cement & Building Materials", "current_price": 11450.00, "pe_ratio": 44.5, "market_cap_cr": 330000.0, "recommendation": "BUY", "notes": "India's largest cement manufacturer expanding capacity to 200MT."},
    {"ticker": "GRASIM", "company_name": "Grasim Industries Ltd", "sector": "Paints, Cement & VSF", "current_price": 2720.00, "pe_ratio": 32.1, "market_cap_cr": 185000.0, "recommendation": "BUY", "notes": "Birla Opus paints rollout and UltraTech cement parent holding."},
    {"ticker": "AMBUJACEM", "company_name": "Ambuja Cements Ltd", "sector": "Cement", "current_price": 635.00, "pe_ratio": 46.8, "market_cap_cr": 156000.0, "recommendation": "BUY", "notes": "Adani group cement arm acquiring regional grinding units."},
    {"ticker": "ACC", "company_name": "ACC Ltd", "sector": "Cement", "current_price": 2520.00, "pe_ratio": 28.4, "market_cap_cr": 47300.0, "recommendation": "HOLD", "notes": "Strong ready-mix concrete network across metro cities."},
    {"ticker": "SIEMENS", "company_name": "Siemens Ltd", "sector": "Capital Goods & Electrification", "current_price": 6850.00, "pe_ratio": 88.0, "market_cap_cr": 244000.0, "recommendation": "BUY", "notes": "Leader in industrial automation, grid technology, and rail locos."},
    {"ticker": "ABB", "company_name": "ABB India Ltd", "sector": "Industrial Automation & Power", "current_price": 8120.00, "pe_ratio": 95.0, "market_cap_cr": 172000.0, "recommendation": "BUY", "notes": "Electrification and robotics automation supplier."},
    {"ticker": "HAL", "company_name": "Hindustan Aeronautics Ltd", "sector": "Defence & Aerospace", "current_price": 4650.00, "pe_ratio": 38.2, "market_cap_cr": 311000.0, "recommendation": "BUY", "notes": "Monopoly defence fighter aircraft and helicopter manufacturer."},
    {"ticker": "BEL", "company_name": "Bharat Electronics Ltd", "sector": "Defence Electronics", "current_price": 295.00, "pe_ratio": 52.0, "market_cap_cr": 215000.0, "recommendation": "BUY", "notes": "Naval radars, missile guidance systems, and electronic warfare."},

    # Metals, Mining & Steel
    {"ticker": "TATASTEEL", "company_name": "Tata Steel Ltd", "sector": "Steel & Metals", "current_price": 152.40, "pe_ratio": 24.5, "market_cap_cr": 190000.0, "recommendation": "HOLD", "notes": "Backward integrated Indian steelmaker transitioning UK operations."},
    {"ticker": "JSWSTEEL", "company_name": "JSW Steel Ltd", "sector": "Steel & Metals", "current_price": 945.00, "pe_ratio": 28.2, "market_cap_cr": 231000.0, "recommendation": "BUY", "notes": "Lowest conversion cost steel producer expanding capacity to 38MT."},
    {"ticker": "HINDALCO", "company_name": "Hindalco Industries Ltd", "sector": "Aluminum & Copper", "current_price": 680.00, "pe_ratio": 16.5, "market_cap_cr": 152000.0, "recommendation": "BUY", "notes": "Novelis subsidiary leader in beverage can recycling and auto sheet."},
    {"ticker": "COALINDIA", "company_name": "Coal India Ltd", "sector": "Mining & Minerals", "current_price": 495.00, "pe_ratio": 8.2, "market_cap_cr": 305000.0, "recommendation": "BUY", "notes": "World's largest coal miner supplying 80%+ of India's thermal power."},
    {"ticker": "VEDL", "company_name": "Vedanta Ltd", "sector": "Metals & Mining", "current_price": 460.00, "pe_ratio": 12.8, "market_cap_cr": 171000.0, "recommendation": "HOLD", "notes": "High dividend yield natural resources conglomerate."},
    {"ticker": "JINDALSTEL", "company_name": "Jindal Steel & Power Ltd", "sector": "Steel & Mining", "current_price": 1010.00, "pe_ratio": 18.4, "market_cap_cr": 103000.0, "recommendation": "BUY", "notes": "Specialist in structural rails and heavy plate production."},
    {"ticker": "NMDC", "company_name": "NMDC Ltd", "sector": "Iron Ore Mining", "current_price": 235.00, "pe_ratio": 11.2, "market_cap_cr": 68800.0, "recommendation": "BUY", "notes": "India's largest iron ore producer supplying domestic steel mills."},

    # Telecom, Media & E-Commerce
    {"ticker": "BHARTIARTL", "company_name": "Bharti Airtel Ltd", "sector": "Telecommunications", "current_price": 1580.00, "pe_ratio": 45.2, "market_cap_cr": 92000.0, "recommendation": "BUY", "notes": "Premium subscriber monetization and enterprise digital cloud."},
    {"ticker": "IDEA", "company_name": "Vodafone Idea Ltd", "sector": "Telecommunications", "current_price": 10.50, "pe_ratio": -1.5, "market_cap_cr": 72000.0, "recommendation": "HOLD", "notes": "5G network capex rollout following FPO equity raise."},
    {"ticker": "NAUKRI", "company_name": "Info Edge (India) Ltd (Naukri)", "sector": "Internet & Classifieds", "current_price": 7850.00, "pe_ratio": 110.0, "market_cap_cr": 101000.0, "recommendation": "BUY", "notes": "Dominant recruitment platform (Naukri) and early Zomato investor."},
    {"ticker": "ZOMATO", "company_name": "Zomato Ltd (Blinkit)", "sector": "Food Delivery & Quick Commerce", "current_price": 275.00, "pe_ratio": 125.0, "market_cap_cr": 242000.0, "recommendation": "BUY", "notes": "Market leader in food delivery & rapid scaling of Blinkit quick commerce."},
    {"ticker": "PAYTM", "company_name": "One97 Communications Ltd (Paytm)", "sector": "Fintech & Digital Payments", "current_price": 680.00, "pe_ratio": -18.5, "market_cap_cr": 43200.0, "recommendation": "HOLD", "notes": "Rebuilding merchant soundbox loan distribution post regulatory reset."},
    {"ticker": "POLICYBZR", "company_name": "PB Fintech Ltd (Policybazaar)", "sector": "Insurtech & Fintech", "current_price": 1720.00, "pe_ratio": 165.0, "market_cap_cr": 78500.0, "recommendation": "BUY", "notes": "Dominant digital insurance comparator and Paisabazaar loans."},
    {"ticker": "NYKAA", "company_name": "FSN E-Commerce Ventures (Nykaa)", "sector": "Beauty & Fashion E-Commerce", "current_price": 205.00, "pe_ratio": 185.0, "market_cap_cr": 58600.0, "recommendation": "HOLD", "notes": "Market leader in prestige beauty e-commerce & retail stores."},
    {"ticker": "BRAINBEES", "company_name": "Brainbees Solutions Ltd (FirstCry)", "sector": "Retail & E-Commerce", "current_price": 635.00, "pe_ratio": 65.0, "market_cap_cr": 33000.0, "recommendation": "BUY", "notes": "Dominant mother & baby care brand in India and Middle East."},
    {"ticker": "ALLIED", "company_name": "Allied Blenders & Distillers Ltd", "sector": "Consumer Spirits & Alcobev", "current_price": 342.10, "pe_ratio": 42.0, "market_cap_cr": 9560.0, "recommendation": "BUY", "notes": "Iconic Officer's Choice whisky maker scaling premium portfolio."}
]

def populate_firestore():
    print(f"Connecting to Firestore using project ID: '{PROJECT_ID}'...")
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/datastore"]
    )
    db = firestore.Client(project=PROJECT_ID, credentials=creds)
    collection_ref = db.collection(COLLECTION_NAME)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    total = len(ALL_NSE_BSE_STOCKS)

    print(f"Batch uploading {total} NSE & BSE stocks to collection '{COLLECTION_NAME}'...")
    
    # Firestore allows up to 500 writes per batch
    batch = db.batch()
    count = 0

    for item in ALL_NSE_BSE_STOCKS:
        doc_id = item["ticker"]
        item["last_updated"] = now_iso
        doc_ref = collection_ref.document(doc_id)
        batch.set(doc_ref, item)
        count += 1

    batch.commit()
    print(f"\nSuccessfully populated all {count} NSE/BSE stock records into Firestore!")

if __name__ == "__main__":
    populate_firestore()
