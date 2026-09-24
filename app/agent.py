# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from pathlib import Path
import time
import uuid
from zoneinfo import ZoneInfo
import google.auth
from google.cloud import firestore, storage

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.load_memory_tool import load_memory_tool
from google.adk.tools.preload_memory_tool import preload_memory_tool
from google import genai
from google.genai import types

try:
    from .a2ui_utils import a2ui_callback
except ImportError:
    from a2ui_utils import a2ui_callback


MODEL = "gemini-2.5-flash"

# CRITICAL: Hardcode GCP Project ID, Bucket Name, and Agent Engine ID as strings.
PROJECT_ID = "qwiklabs-gcp-01-37b29569bd39"
COLLECTION_NAME = "indian_stocks"
BUCKET_NAME = "dalalstreet-ai-media-qwiklabs-gcp-01-37b29569bd39"
AGENT_ENGINE_ID = "4697036708045127680"

# Memory Bank Service configuration for deployment & memory retention
memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location="us-east1",
    agent_engine_id=AGENT_ENGINE_ID,
)

# Build A2UI v0.8 System Prompt using A2uiSchemaManager & BasicCatalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are DalalStreet AI, an expert Indian stock market advisor and portfolio analyst. "
        "You have access to a persistent Memory Bank (remember and track all user health information, dietary restrictions, and user ALLERGIES). "
        "You can analyze company financial statements, balance sheets, income statements, and annual reports to project future revenue, net profit, EPS, and target valuations using analyze_company_books, calculate_dcf_valuation, calculate_cagr, or custom Python code in your execution sandbox. "
        "You can search stocks by partial company name, brand, or symbol (e.g. 'Tata', 'FirstCry', 'Infosys', 'Airtel', 'Maruti', 'HDFC', 'Reliance') using search_stocks_in_db and get_stock_from_db. "
        "You can execute Python code safely in a sandbox, calculate Compound Annual Growth Rate (CAGR), perform DCF intrinsic valuations, generate stock infographic banners, generate short animated stock market videos using Google Omni model (gemini-omni-flash-preview), geocode addresses, find nearby banks/branches using Google Maps, fetch live exchange rates (USD/INR), real-time stock prices, inspect stored stocks in the database, and manage stock records for NSE/BSE companies."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


def _get_firestore_client() -> firestore.Client:
    """Helper function to create a Firestore client with hardcoded project ID and required scopes."""
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/datastore"]
    )
    return firestore.Client(project=PROJECT_ID, credentials=creds)


def _get_code_executor():
    """Helper to initialize AgentEngineSandboxCodeExecutor from deployment_metadata.json."""
    metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            sandbox_id = metadata.get("sandbox_resource_name")
            engine_id = metadata.get("remote_agent_runtime_id")
            if sandbox_id:
                return AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox_id)
            elif engine_id:
                return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=engine_id)
        except Exception:
            pass
    return None


def generate_stock_infographic_image(
    prompt: str,
    tool_context: ToolContext,
) -> str:
    """Generates an image for an item in the Indian stock market domain using Gemini image generation model.

    Args:
        prompt: Detailed description of the image to generate (e.g. 'Infographic banner for Reliance Industries stock analysis').
        tool_context: ADK ToolContext to register artifacts in the Playground.

    Returns:
        The public HTTPS URL of the generated image uploaded to Cloud Storage.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        res = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        if not res.candidates or not res.candidates[0].content.parts:
            return "Error: Model did not return any image candidates."

        part = res.candidates[0].content.parts[0]
        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/png"
        ext = "jpg" if "jpeg" in mime_type else "png"
        filename = f"stock_image_{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save artifact to ADK ToolContext for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes directly to GCS bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated stock infographic image.\n- Public URL: {public_url}\n- Artifact File: {filename}"
    except Exception as e:
        return f"Error generating stock image: {str(e)}"


def generate_stock_video(
    prompt: str,
    tool_context: ToolContext,
) -> str:
    """Generates a short animated video for an item in the Indian stock market domain using Google's Omni model (gemini-omni-flash-preview).

    Args:
        prompt: Detailed description of the stock market video to generate (e.g. 'Animated 3D stock ticker chart rising on Dalal Street for Reliance Industries').
        tool_context: ADK ToolContext to register artifacts in the Playground.

    Returns:
        The public HTTPS URL of the generated video uploaded to Cloud Storage.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        res = client.models.generate_content(
            model="gemini-omni-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["VIDEO"]),
        )

        if not res.candidates or not res.candidates[0].content.parts:
            return "Error: Model did not return any video candidates."

        part = res.candidates[0].content.parts[0]
        video_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "video/mp4"
        ext = "mp4" if "mp4" in mime_type else "webm"
        filename = f"stock_video_{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save artifact to ADK ToolContext for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes directly to GCS bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated stock video.\n- Public URL: {public_url}\n- Artifact File: {filename}"
    except Exception as e:
        return f"Error generating stock video: {str(e)}"


def geocode_address(address: str) -> str:
    """Converts a street address or location name into geographic coordinates (latitude and longitude) using the Google Geocoding API.

    Args:
        address: The address or location to geocode (e.g. 'Dalal Street Mumbai', 'BSE Building, Fort').

    Returns:
        A string containing the formatted address, latitude, and longitude.
    """
    try:
        import requests

        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            return f"Could not geocode address '{address}'. Status: {data.get('status')}"

        result = data["results"][0]
        formatted_address = result.get("formatted_address", address)
        location = result.get("geometry", {}).get("location", {})
        lat, lng = location.get("lat"), location.get("lng")

        return f"Geocoding Result for '{address}':\n- Formatted Address: {formatted_address}\n- Latitude: {lat}\n- Longitude: {lng}"
    except Exception as e:
        return f"Error geocoding address '{address}': {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "bank",
    radius_meters: float = 1000.0,
    max_results: int = 5,
) -> str:
    """Finds nearby places of a specific type around geographic coordinates using the Google Places API (New).

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Place type category (e.g. 'bank', 'atm', 'finance', 'office').
        radius_meters: Search radius in meters (default 1000.0).
        max_results: Maximum number of results to return (default 5).

    Returns:
        A string listing nearby places with their name, address, and coordinates.
    """
    try:
        import requests

        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
            "Content-Type": "application/json",
        }
        payload = {
            "includedTypes": [place_type.lower()],
            "maxResultCount": min(max_results, 20),
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": radius_meters,
                }
            },
        }

        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code != 200:
            return f"Error: Places API returned HTTP {response.status_code}: {response.text}"

        data = response.json()
        places = data.get("places", [])
        if not places:
            return f"No nearby '{place_type}' places found within {radius_meters}m radius."

        results = []
        for idx, p in enumerate(places, 1):
            name = p.get("displayName", {}).get("text", "N/A")
            addr = p.get("formattedAddress", "N/A")
            loc = p.get("location", {})
            lat, lng = loc.get("latitude"), loc.get("longitude")
            results.append(f"{idx}. {name}\n   Address: {addr}\n   Location: ({lat}, {lng})")

        return f"Nearby '{place_type}' places around ({latitude}, {longitude}):\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error searching nearby places: {str(e)}"


def get_forex_rates(base_currency: str = "USD") -> str:
    """Fetches real-time foreign exchange (Forex) rates against Indian Rupee (INR) and major currencies.

    Args:
        base_currency: The base currency code (default 'USD', or 'EUR', 'GBP', 'JPY').

    Returns:
        A string with current exchange rates against INR and key international currencies.
    """
    try:
        import requests

        base = base_currency.strip().upper()
        url = f"https://api.frankfurter.app/latest?from={base}"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return f"Could not fetch forex rates for base currency '{base}'."

        data = response.json()
        rates = data.get("rates", {})
        date_str = data.get("date", "Latest")

        inr_rate = rates.get("INR", "N/A")
        eur_rate = rates.get("EUR", "N/A")
        gbp_rate = rates.get("GBP", "N/A")

        return (
            f"Forex Rates for {base} (Date: {date_str}):\n"
            f"- 1 {base} = ₹{inr_rate} INR\n"
            f"- 1 {base} = €{eur_rate} EUR\n"
            f"- 1 {base} = £{gbp_rate} GBP"
        )
    except Exception as e:
        return f"Error fetching forex rates for '{base_currency}': {str(e)}"


def fetch_live_stock_price(ticker: str) -> str:
    """Fetches real-time stock price and 52-week trading metrics for Indian stocks (NSE/BSE).

    Args:
        ticker: The stock ticker symbol (e.g. 'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'TATAMOTORS').

    Returns:
        A string with the real-time stock price, day change, and 52-week range.
    """
    try:
        import requests

        clean_symbol = ticker.strip().upper()
        if not (clean_symbol.endswith(".NS") or clean_symbol.endswith(".BO")):
            clean_symbol = f"{clean_symbol}.NS"

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_symbol}?interval=1d&range=1d"
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            return f"Error: Received HTTP {response.status_code} fetching stock data for '{clean_symbol}'."

        data = response.json()
        chart_result = data.get("chart", {}).get("result")
        if not chart_result:
            return f"Could not find live market data for symbol '{clean_symbol}'."

        meta = chart_result[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose")
        currency = meta.get("currency", "INR")
        high_52 = meta.get("fiftyTwoWeekHigh")
        low_52 = meta.get("fiftyTwoWeekLow")
        exchange = meta.get("exchangeName", "NSE")

        change = round(price - prev_close, 2) if price and prev_close else 0.0
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
        sign = "+" if change >= 0 else ""

        return (
            f"Live Market Data for {clean_symbol} ({exchange}):\n"
            f"- Current Price: ₹{price:,.2f} {currency}\n"
            f"- Today's Change: {sign}{change:,.2f} ({sign}{change_pct:.2f}%)\n"
            f"- Previous Close: ₹{prev_close:,.2f}\n"
            f"- 52-Week Range: ₹{low_52:,.2f} - ₹{high_52:,.2f}"
        )
    except Exception as e:
        return f"Error fetching live stock price for '{ticker}': {str(e)}"


def calculate_dcf_valuation(
    current_fcf_cr: float,
    shares_cr: float,
    growth_rate_pct: float = 10.0,
    discount_rate_pct: float = 12.0,
    terminal_growth_pct: float = 4.0,
    projection_years: int = 5,
) -> str:
    """Calculates intrinsic fair value per share for a company using a 5-year Discounted Cash Flow (DCF) model.

    Args:
        current_fcf_cr: Current Annual Free Cash Flow in Crores INR (e.g. 5000.0).
        shares_cr: Total outstanding shares in Crores (e.g. 100.0).
        growth_rate_pct: Expected annual FCF growth rate percentage for next 5 years (default 10.0%).
        discount_rate_pct: Discount rate / WACC percentage (default 12.0%).
        terminal_growth_pct: Perpetual terminal growth rate percentage (default 4.0%).
        projection_years: Projection period in years (default 5).

    Returns:
        A string with projected cash flows, terminal value, total equity value, and intrinsic value per share.
    """
    try:
        g = growth_rate_pct / 100.0
        r = discount_rate_pct / 100.0
        g_t = terminal_growth_pct / 100.0

        if r <= g_t:
            return "Error: Discount rate must be strictly greater than terminal growth rate."

        pv_fcf_total = 0.0
        fcf = current_fcf_cr

        for yr in range(1, projection_years + 1):
            fcf = fcf * (1 + g)
            pv = fcf / ((1 + r) ** yr)
            pv_fcf_total += pv

        terminal_value = (fcf * (1 + g_t)) / (r - g_t)
        pv_terminal_value = terminal_value / ((1 + r) ** projection_years)
        total_enterprise_value = pv_fcf_total + pv_terminal_value
        intrinsic_value_per_share = (total_enterprise_value / shares_cr) if shares_cr > 0 else 0.0

        return (
            f"DCF Valuation Calculation Summary:\n"
            f"- Annual FCF: ₹{current_fcf_cr:,.1f} Cr | Outstanding Shares: {shares_cr:,.1f} Cr\n"
            f"- Discount Rate (WACC): {discount_rate_pct}%\n"
            f"- Projected FCF Growth Rate: {growth_rate_pct}%\n"
            f"- Terminal Growth Rate: {terminal_growth_pct}%\n"
            f"- Sum PV of {projection_years}-Year FCF: ₹{pv_fcf_total:,.2f} Cr\n"
            f"- PV of Terminal Value: ₹{pv_terminal_value:,.2f} Cr\n"
            f"- Intrinsic Enterprise Value: ₹{total_enterprise_value:,.2f} Cr\n"
            f"- Estimated Fair Value per Share: ₹{intrinsic_value_per_share:,.2f}"
        )
    except Exception as e:
        return f"Error computing DCF valuation: {str(e)}"


# Performance & Scalability: In-memory TTL cache (300 seconds expiration)
_STOCK_CACHE = {}
_ALL_STOCKS_CACHE = {"timestamp": 0, "data": None}
_CACHE_TTL_SECONDS = 300


def search_stocks_in_db(query: str) -> str:
    """Searches Indian stocks in the Firestore database by partial company name, brand, ticker, or sector keyword.

    Args:
        query: Partial stock name, brand, ticker symbol, or sector (e.g. 'Tata', 'FirstCry', 'Airtel', 'Maruti', 'HDFC', 'Infosys', 'Reliance', 'IT', 'Banking').

    Returns:
        A list of matching stock records found in the database.
    """
    try:
        if not query or not query.strip():
            return "Please provide a search term (e.g., 'Tata', 'FirstCry', 'Infosys', 'Airtel')."

        search_term = query.strip().lower()
        db = _get_firestore_client()
        docs = db.collection(COLLECTION_NAME).stream()

        matches = []
        for doc in docs:
            data = doc.to_dict()
            t_str = data.get("ticker", "").lower()
            name_str = data.get("company_name", "").lower()
            sec_str = data.get("sector", "").lower()
            notes_str = data.get("notes", "").lower()

            if (search_term in t_str) or (search_term in name_str) or (search_term in sec_str) or (search_term in notes_str):
                matches.append(
                    f"• [{data.get('ticker')}] {data.get('company_name')} ({data.get('sector')}) - "
                    f"Price: ₹{data.get('current_price', 0):,.2f} | P/E: {data.get('pe_ratio')} | Rec: {data.get('recommendation')}\n"
                    f"  Notes: {data.get('notes')}"
                )

        if not matches:
            return f"No stocks matching search term '{query}' were found in the database."

        return f"Found {len(matches)} Stock(s) matching '{query}':\n" + "\n\n".join(matches)
    except Exception as e:
        return f"Error searching stocks in Firestore: {str(e)}"


def get_stock_from_db(ticker: str) -> str:
    """Fetches details for a specific Indian stock from the Firestore database, supporting exact ticker or partial stock name matching.

    Args:
        ticker: The stock ticker symbol or partial company name (e.g. 'RELIANCE', 'TCS', 'INFY', 'Tata Motors', 'FirstCry', 'Airtel', 'Maruti').

    Returns:
        A text description of the stock data found in the database.
    """
    try:
        clean_ticker = ticker.strip().upper().replace(".NS", "").replace(".BO", "")
        now = time.time()

        # Check in-memory cache first for exact ticker match
        if clean_ticker in _STOCK_CACHE:
            cached_time, data = _STOCK_CACHE[clean_ticker]
            if now - cached_time < _CACHE_TTL_SECONDS:
                return (
                    f"Database Record for {data.get('company_name')} ({clean_ticker}) [⚡ Cached Response]:\n"
                    f"- Sector: {data.get('sector')}\n"
                    f"- Stored Price: ₹{data.get('current_price'):,.2f}\n"
                    f"- P/E Ratio: {data.get('pe_ratio')}\n"
                    f"- Market Cap: ₹{data.get('market_cap_cr'):,.2f} Cr\n"
                    f"- Recommendation: {data.get('recommendation')}\n"
                    f"- Notes: {data.get('notes')}\n"
                    f"- Last Updated: {data.get('last_updated')}"
                )

        db = _get_firestore_client()
        doc_ref = db.collection(COLLECTION_NAME).document(clean_ticker)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            _STOCK_CACHE[clean_ticker] = (now, data)
            return (
                f"Database Record for {data.get('company_name')} ({clean_ticker}):\n"
                f"- Sector: {data.get('sector')}\n"
                f"- Stored Price: ₹{data.get('current_price'):,.2f}\n"
                f"- P/E Ratio: {data.get('pe_ratio')}\n"
                f"- Market Cap: ₹{data.get('market_cap_cr'):,.2f} Cr\n"
                f"- Recommendation: {data.get('recommendation')}\n"
                f"- Notes: {data.get('notes')}\n"
                f"- Last Updated: {data.get('last_updated')}"
            )

        # Fallback: Smart partial stock name search
        return search_stocks_in_db(ticker)
    except Exception as e:
        return f"Error retrieving stock '{ticker}' from Firestore: {str(e)}"



def list_all_stocks_in_db() -> str:
    """Lists Indian stocks stored in the Firestore database using field projections and caching for performance.

    Returns:
        A summary string listing tracked stocks and their basic metrics.
    """
    try:
        now = time.time()
        if _ALL_STOCKS_CACHE["data"] and (now - _ALL_STOCKS_CACHE["timestamp"] < _CACHE_TTL_SECONDS):
            return "Tracked Indian Stocks in Database [⚡ Cached High-Performance Response]:\n" + _ALL_STOCKS_CACHE["data"]

        db = _get_firestore_client()
        # Projections: select only essential summary fields to reduce network bandwidth and payload size
        docs = db.collection(COLLECTION_NAME).select(
            ["ticker", "company_name", "sector", "current_price", "pe_ratio", "recommendation"]
        ).stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append(
                f"• [{data.get('ticker')}] {data.get('company_name')} ({data.get('sector')}) - "
                f"Price: ₹{data.get('current_price', 0):,.2f} | P/E: {data.get('pe_ratio')} | Rec: {data.get('recommendation')}"
            )

        if not results:
            return "No stocks found in the database."

        formatted_result = "\n".join(results)
        _ALL_STOCKS_CACHE["timestamp"] = now
        _ALL_STOCKS_CACHE["data"] = formatted_result

        return "Tracked Indian Stocks in Database:\n" + formatted_result
    except Exception as e:
        return f"Error listing stocks from Firestore: {str(e)}"


def add_or_update_stock_in_db(
    ticker: str,
    company_name: str,
    sector: str,
    current_price: float,
    pe_ratio: float,
    market_cap_cr: float,
    recommendation: str,
    notes: str = "",
) -> str:
    """Adds a new stock or updates an existing stock record in the Firestore database.

    Args:
        ticker: The stock symbol (e.g. 'RELIANCE', 'TCS').
        company_name: Full name of the company.
        sector: Industry sector (e.g. 'IT Services', 'Banking').
        current_price: Current market price in INR.
        pe_ratio: Price-to-Earnings ratio.
        market_cap_cr: Market capitalization in Crores INR.
        recommendation: Analyst recommendation ('BUY', 'HOLD', 'SELL').
        notes: Key investment rationale or notes.

    Returns:
        A confirmation message string.
    """
    try:
        db = _get_firestore_client()
        clean_ticker = ticker.strip().upper().replace(".NS", "").replace(".BO", "")
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        stock_data = {
            "ticker": clean_ticker,
            "company_name": company_name,
            "sector": sector,
            "current_price": float(current_price),
            "pe_ratio": float(pe_ratio),
            "market_cap_cr": float(market_cap_cr),
            "recommendation": recommendation.upper(),
            "notes": notes,
            "last_updated": now_iso,
        }
        db.collection(COLLECTION_NAME).document(clean_ticker).set(stock_data)

        # Invalidate in-memory caches to maintain consistency
        _STOCK_CACHE.pop(clean_ticker, None)
        _ALL_STOCKS_CACHE["data"] = None

        return f"Successfully saved stock '{clean_ticker}' ({company_name}) to Firestore."
    except Exception as e:
        return f"Error saving stock '{ticker}' to Firestore: {str(e)}"


def calculate_cagr(
    beginning_value: float,
    ending_value: float,
    years: float = 5.0,
) -> str:
    """Calculates the Compound Annual Growth Rate (CAGR) for a stock, revenue, or investment portfolio.

    Args:
        beginning_value: Initial investment or historical stock price/revenue.
        ending_value: Final investment or current stock price/revenue.
        years: Time period in years (default: 5.0).

    Returns:
        A detailed summary string with the calculated CAGR percentage.
    """
    try:
        if beginning_value <= 0 or ending_value <= 0 or years <= 0:
            return "Error: Beginning value, ending value, and years must be greater than zero."

        cagr = ((ending_value / beginning_value) ** (1.0 / years) - 1.0) * 100.0
        total_return = ((ending_value - beginning_value) / beginning_value) * 100.0

        return (
            f"Compound Annual Growth Rate (CAGR) Calculation:\n"
            f"- Beginning Value: ₹{beginning_value:,.2f}\n"
            f"- Ending Value: ₹{ending_value:,.2f}\n"
            f"- Period: {years} Years\n"
            f"- Total Growth Return: {total_return:+.2f}%\n"
            f"- CAGR: {cagr:.2f}% per annum"
        )
    except Exception as e:
        return f"Error calculating CAGR: {str(e)}"


def analyze_company_books(
    ticker_or_name: str,
    revenue_cr: float,
    net_profit_cr: float,
    operating_margin_pct: float,
    revenue_cagr_pct: float = 12.0,
    projection_years: int = 3,
    outstanding_shares_cr: float = 100.0,
) -> str:
    """Analyzes company financial books and generates multi-year revenue, profit, EPS, and valuation projections.

    Args:
        ticker_or_name: Stock ticker or company name (e.g. 'RELIANCE', 'TCS', 'INFY', 'Tata Motors', 'FirstCry').
        revenue_cr: Current annual revenue in Crores INR (e.g. 50000.0).
        net_profit_cr: Current annual net profit in Crores INR (e.g. 8000.0).
        operating_margin_pct: Current operating margin percentage (e.g. 18.5).
        revenue_cagr_pct: Expected revenue CAGR percentage for projections (default: 12.0%).
        projection_years: Number of forecast years (default: 3).
        outstanding_shares_cr: Total outstanding shares in Crores (default: 100.0).

    Returns:
        A formatted 3-statement financial projection summary with forecasted EPS and valuation estimates.
    """
    try:
        if revenue_cr <= 0 or projection_years <= 0:
            return "Error: Revenue and projection years must be greater than zero."

        net_margin = (net_profit_cr / revenue_cr) if revenue_cr > 0 else 0.15
        current_eps = net_profit_cr / outstanding_shares_cr if outstanding_shares_cr > 0 else 0.0

        projections = []
        proj_rev = revenue_cr
        proj_profit = net_profit_cr

        for year in range(1, projection_years + 1):
            proj_rev *= (1.0 + (revenue_cagr_pct / 100.0))
            proj_profit = proj_rev * net_margin
            proj_eps = proj_profit / outstanding_shares_cr if outstanding_shares_cr > 0 else 0.0
            projections.append(
                f"• Year {year}: Projected Revenue = ₹{proj_rev:,.2f} Cr | Net Profit = ₹{proj_profit:,.2f} Cr | EPS = ₹{proj_eps:,.2f}"
            )

        implied_pe = 25.0
        target_price = (proj_profit / outstanding_shares_cr) * implied_pe if outstanding_shares_cr > 0 else 0.0

        return (
            f"Financial Books & Multi-Year Projection Model for {ticker_or_name}:\n"
            f"--- Baseline Metrics ---\n"
            f"- Base Revenue: ₹{revenue_cr:,.2f} Cr\n"
            f"- Base Net Profit: ₹{net_profit_cr:,.2f} Cr (Net Margin: {net_margin * 100:.2f}%)\n"
            f"- Operating Margin: {operating_margin_pct:.2f}%\n"
            f"- Current EPS: ₹{current_eps:,.2f}\n"
            f"- Assumed Revenue CAGR: {revenue_cagr_pct:.2f}%\n\n"
            f"--- Forecasted Financials ({projection_years}-Year Horizon) ---\n" +
            "\n".join(projections) +
            f"\n\n--- Valuation Target Estimate ---\n"
            f"- Implied Target Price (at {implied_pe}x P/E): ₹{target_price:,.2f} per share"
        )
    except Exception as e:
        return f"Error building financial projection model: {str(e)}"


root_agent = Agent(
    name="simple_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    after_model_callback=a2ui_callback,
    code_executor=_get_code_executor(),
    tools=[
        preload_memory_tool,
        load_memory_tool,
        generate_stock_infographic_image,
        generate_stock_video,
        geocode_address,
        find_nearby_places,
        get_forex_rates,
        fetch_live_stock_price,
        calculate_dcf_valuation,
        calculate_cagr,
        analyze_company_books,
        search_stocks_in_db,
        get_stock_from_db,
        list_all_stocks_in_db,
        add_or_update_stock_in_db,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)



