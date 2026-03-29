import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import json
import os

st.set_page_config(page_title="Sravan's QGARP Command Center v8.4", layout="wide")

# --- PERSISTENT CONFIGURATION MANAGEMENT ---
CONFIG_FILE = "portfolio_config.json"

# Default baseline if the file doesn't exist yet
DEFAULT_CONFIG = {
    "CORE_HOLDINGS": {
        "ASIANPAINT.NS": {"Qty": 11}, 
        "NESTLEIND.NS": {"Qty": 20}, 
        "PIDILITIND.NS": {"Qty": 17}, 
        "HDFCBANK.NS": {"Qty": 28}, 
        "TCS.NS": {"Qty": 10}, 
        "ITC.NS": {"Qty": 80}
    },
    "DEBT_HOLDINGS": {
        "Kotak Arbitrage Fund": {"Ticker": "0P0000XV5S.BO", "Qty": 0.00, "Fallback_NAV": 34.00} 
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Load the live data from the JSON file
app_config = load_config()
CORE_HOLDINGS = app_config["CORE_HOLDINGS"]
DEBT_HOLDINGS = app_config["DEBT_HOLDINGS"]
CORE_PORTFOLIO = list(CORE_HOLDINGS.keys())

# --- FAMILY SATELLITES (Static) ---
FAMILY_PORTFOLIO = {
    "ATHERENERG.NS": {"Qty": 250, "Entry Price": 425.60},     
    "IREDA.NS": {"Qty": 480, "Entry Price": 141.37},     
    "KPIGREEN.NS": {"Qty": 93, "Entry Price": 486.57},   
    "SUZLON.NS": {"Qty": 302, "Entry Price": 46.52},     
    "KEC.NS": {"Qty": 78, "Entry Price": 589.67},        
    "JUNIORBEES.NS": {"Qty": 35, "Entry Price": 722.99}, 
    "HDFCSML250.NS": {"Qty": 157, "Entry Price": 156.25} 
}

NIFTY_TICKERS = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", 
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", 
    "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", 
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", 
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS", 
    "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", 
    "LTIM.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", 
    "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", 
    "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", 
    "TITAN.NS", "TRENT.NS", "ULTRACEMCO.NS", "WIPRO.NS"
]

EXCLUDE_LIST = [
    "COALINDIA.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BPCL.NS", "SBIN.NS", 
    "TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", 
    "TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", 
    "ADANIENT.NS", "ADANIPORTS.NS" 
]

SCAN_LIST = CORE_PORTFOLIO + list(FAMILY_PORTFOLIO.keys()) + [t for t in NIFTY_TICKERS if t not in CORE_PORTFOLIO and t not in FAMILY_PORTFOLIO.keys() and t not in EXCLUDE_LIST]

CORE_OVERRIDES = {
    "TCS.NS": 0.60, "HDFCBANK.NS": 0.65, "ITC.NS": 0.54,
    "NESTLEIND.NS": 2.00, "ASIANPAINT.NS": 1.80, "PIDILITIND.NS": 1.80
}

FAMILY_OVERRIDES = {
    "IREDA.NS": 0.60, "KPIGREEN.NS": 0.65, "SUZLON.NS": 0.65,
    "KEC.NS": 0.85, "ATHERENERG.NS": 1.00
}

BASE_SECTOR_MULTIPLIERS = {
    "Consumer Defensive": 1.20,
    "Consumer Cyclical": 1.00,
    "Communication Services": 1.00,
    "Industrials": 1.00,
    "Financial Services": 0.55,
    "Technology": 0.60,
    "Healthcare": 1.20
}

# --- SIDEBAR CONFIGURATION ---
st.sidebar.image("https://img.icons8.com/color/96/000000/combo-chart--v1.png", width=60)
st.sidebar.title("System Controls")
sip_capital = st.sidebar.number_input("Monthly SIP Capital (₹)", min_value=1000, value=30000, step=5000)

# The Persistent UI logic
with st.sidebar.expander("⚙️ Update Portfolio Quantities", expanded=False):
    with st.form("update_holdings_form"):
        st.write("Update your core shares and fund units. Changes save permanently.")
        
        st.markdown("**Core Equity (Shares)**")
        new_core = {}
        for ticker, data in CORE_HOLDINGS.items():
            new_core[ticker] = {"Qty": st.number_input(ticker, min_value=0, value=int(data["Qty"]), step=1)}
            
        st.markdown("**Dry Powder (Units)**")
        new_debt = {}
        for fund, data in DEBT_HOLDINGS.items():
            new_debt[fund] = {
                "Ticker": data["Ticker"],
                "Qty": st.number_input(fund, min_value=0.0, value=float(data["Qty"]), step=1.0, format="%.3f"),
                "Fallback_NAV": data["Fallback_NAV"]
            }
            
        if st.form_submit_button("💾 Save Changes to Disk"):
            app_config["CORE_HOLDINGS"] = new_core
            app_config["DEBT_HOLDINGS"] = new_debt
            save_config(app_config)
            st.success("Holdings saved securely!")
            st.rerun()

st.sidebar.caption("v8.4 Engine dynamically routes capital, outputs broker-ready orders, and persists your holdings seamlessly.")

# --- UI HELPER FUNCTIONS ---
def safe_float(info_dict, key, default=0.0):
    try:
        val = info_dict.get(key)
        if val is None or str(val).strip().upper() in ['N/A', '-', 'NAN', '']:
            return float(default)
        return float(str(val).replace(',', '').replace('%', ''))
    except (ValueError, TypeError):
        return float(default)

def format_df(df, drop_score=True):
    if df.empty: return df
    cols_to_drop = ["Ticker"]
    if drop_score and "Numeric Score" in df.columns:
        cols_to_drop.append("Numeric Score")
        
    df_disp = df.drop(columns=[col for col in cols_to_drop if col in df.columns]).sort_values(by="Buffett Score", ascending=False).reset_index(drop=True)
    if "Live Price" in df_disp.columns: df_disp["Live Price"] = df_disp["Live Price"].apply(lambda x: f"₹{x:,.2f}")
    if "Live EPS" in df_disp.columns: df_disp["Live EPS"] = df_disp["Live EPS"].apply(lambda x: "N/A" if x <= 0 else f"₹{x:,.2f}")
    if "Growth (%)" in df_disp.columns: df_disp["Growth (%)"] = df_disp["Growth (%)"].apply(lambda x: f"{x}%") 
    if "Target (₹)" in df_disp.columns: df_disp["Target (₹)"] = df_disp.apply(lambda row: "N/A" if ("ETF" in row["Action"] or "PRE-PROFIT" in row["Action"]) else f"₹{row['Target (₹)']:,.0f}", axis=1)
    if "Distance (%)" in df_disp.columns: df_disp["Distance (%)"] = df_disp.apply(lambda row: "N/A" if ("ETF" in row["Action"] or "PRE-PROFIT" in row["Action"]) else f"{row['Distance (%)']}%", axis=1)
    if "Actual Wt (%)" in df_disp.columns: df_disp["Actual Wt (%)"] = df_disp["Actual Wt (%)"].apply(lambda x: f"{x:.2f}%")
    if "Target Wt (%)" in df_disp.columns: df_disp["Target Wt (%)"] = df_disp["Target Wt (%)"].apply(lambda x: f"{x:.2f}%")
    if "Deviation (%)" in df_disp.columns: df_disp["Deviation (%)"] = df_disp["Deviation (%)"].apply(lambda x: f"{x:+.2f}%")
    if "Numeric Score" in df_disp.columns: df_disp["Numeric Score"] = df_disp["Numeric Score"].apply(lambda x: f"{x:.1f}")
    if "Executed (₹)" in df_disp.columns: df_disp["Executed (₹)"] = df_disp["Executed (₹)"].apply(lambda x: f"₹{x:,.2f}")
    return df_disp

def highlight_action(s):
    if '✅' in s['Action']: return ['background-color: rgba(0, 255, 0, 0.2)'] * len(s)
    elif '⚠️' in s['Action']: return ['background-color: rgba(255, 255, 0, 0.2)'] * len(s)
    elif '🔥' in s['Action']: return ['background-color: rgba(255, 0, 0, 0.4)'] * len(s)
    elif '🚨' in s['Action']: return ['background-color: rgba(255, 100, 0, 0.3)'] * len(s)
    elif '🟠' in s['Action']: return ['background-color: rgba(255, 165, 0, 0.2)'] * len(s)
    elif '☠️' in s['Action']: return ['background-color: rgba(0, 0, 0, 0.8); color: white'] * len(s)
    elif 'GLITCH' in s['Action']: return ['background-color: rgba(128, 128, 128, 0.3)'] * len(s)
    elif '🚀' in s['Action']: return ['background-color: rgba(147, 112, 219, 0.3)'] * len(s)
    return [''] * len(s)

def highlight_family(s):
    row_styles = [''] * len(s)
    if '✅' in s['Action']: row_styles = ['background-color: rgba(0, 255, 0, 0.2)'] * len(s)
    elif '⚠️' in s['Action']: row_styles = ['background-color: rgba(255, 255, 0, 0.2)'] * len(s)
    elif '🔥' in s['Action']: row_styles = ['background-color: rgba(255, 0, 0, 0.4)'] * len(s)
    elif '🚨' in s['Action']: row_styles = ['background-color: rgba(255, 100, 0, 0.3)'] * len(s)
    elif '🟠' in s['Action']: row_styles = ['background-color: rgba(255, 165, 0, 0.2)'] * len(s)
    elif '☠️' in s['Action']: row_styles = ['background-color: rgba(0, 0, 0, 0.8); color: white'] * len(s)
    elif 'GLITCH' in s['Action']: row_styles = ['background-color: rgba(128, 128, 128, 0.3)'] * len(s)
    elif '📈' in s['Action']: row_styles = ['background-color: rgba(173, 216, 230, 0.4)'] * len(s)
    elif '🚀' in s['Action']: row_styles = ['background-color: rgba(147, 112, 219, 0.3)'] * len(s)
    
    try:
        pnl_idx = s.index.get_loc('P&L (%)')
        pnl_str = str(s['P&L (%)']).replace('%', '').replace('+', '')
        pnl_val = float(pnl_str)
        if pnl_val > 0: row_styles[pnl_idx] = 'color: #00FF00; font-weight: bold'
        elif pnl_val < 0: row_styles[pnl_idx] = 'color: #FF0000; font-weight: bold'
    except: pass
    return row_styles

# --- CACHING & BATCH FETCH ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market_data(scan_list_param):
    all_data = []
    errors = []
    
    tickers_string = " ".join(scan_list_param)
    tickers_obj = yf.Tickers(tickers_string)
    
    for i, ticker in enumerate(scan_list_param):
        try:
            try:
                stock = tickers_obj.tickers[ticker]
                info = stock.info
            except Exception:
                stock = yf.Ticker(ticker)
                info = stock.info
            
            if not info or ('currentPrice' not in info and 'regularMarketPrice' not in info):
                last_price = stock.fast_info.get('lastPrice', 0.0)
                if last_price > 0:
                    info['currentPrice'] = last_price
                    
            price = safe_float(info, 'currentPrice', safe_float(info, 'regularMarketPrice', 0.0))
            eps = safe_float(info, 'trailingEps', safe_float(info, 'forwardEps', 0.0))
            is_etf = ticker in ["JUNIORBEES.NS", "HDFCSML250.NS"]
            roe = safe_float(info, 'returnOnEquity', 0.0)
            if roe == 0.0:
                book_value = safe_float(info, 'bookValue', 0.0)
                if book_value > 0 and eps > 0: roe = eps / book_value
            roe = roe * 100
            profit_margin = safe_float(info, 'profitMargins', 0.0)
            if profit_margin == 0.0:
                revenue_per_share = safe_float(info, 'revenuePerShare', 0.0)
                if revenue_per_share > 0 and eps > 0: profit_margin = eps / revenue_per_share
            profit_margin = profit_margin * 100
            raw_debt = safe_float(info, 'debtToEquity', 0.0)
            debt_eq = raw_debt / 100 if raw_debt > 1.0 else raw_debt
            growth = safe_float(info, 'earningsGrowth', 0.0) * 100
            if growth == 0: growth = safe_float(info, 'revenueGrowth', 0.0) * 100
            fcf = safe_float(info, 'freeCashflow', 0.0)
            sector = info.get('sector', '')
            industry = info.get('industry', '')

            # --- 1. THE QUALITY ENGINE ---
            moat_score = (roe / 4) + (profit_margin / 4)
            moat_score = min(10.0, max(0.0, moat_score))
            fin_score = 0.0
            if roe > 25: fin_score += 5
            elif roe > 15: fin_score += 3
            if sector == 'Financial Services': fin_score += 5 
            else:
                if debt_eq < 0.5: fin_score += 5
                elif debt_eq < 1.0: fin_score += 3
            cons_score = 0.0
            if eps > 0: cons_score += 2
            if profit_margin > 10: cons_score += 3
            if fcf > 0: cons_score += 2.0 
            growth_score = min(5.0, max(0.0, growth / 5.0))
            quality_score = moat_score + fin_score + cons_score + growth_score
            
            # --- 1.5. DYNAMIC GROWTH OVERRIDES ---
            if ticker == "KEC.NS" and profit_margin < 8.0: quality_score += 8.0  
            elif ticker in ["IREDA.NS", "KPIGREEN.NS"] and roe < 20.0: quality_score += 2.0  
            elif ticker == "ATHERENERG.NS" and eps <= 0: quality_score += 5.0  
            elif ticker == "SUZLON.NS" and debt_eq > 0.1: quality_score += 1.0  
            quality_score = min(25.0, quality_score)
            base_pe = 10 + (quality_score * 1.0)
            
            # --- 2. MULTIPLIERS & CALIBRATION ---
            if ticker in CORE_OVERRIDES: sector_multiplier = CORE_OVERRIDES[ticker]
            elif ticker in FAMILY_OVERRIDES: sector_multiplier = FAMILY_OVERRIDES[ticker]
            elif ticker == 'RELIANCE.NS': sector_multiplier = 1.00 
            else:
                sector_multiplier = BASE_SECTOR_MULTIPLIERS.get(sector, 1.00)
                if sector == 'Consumer Defensive':
                    if industry == 'Tobacco': sector_multiplier = 0.54
                    elif roe > 50: sector_multiplier = 2.00  
                    elif roe > 15: sector_multiplier = 1.80  
                elif sector in ['Consumer Cyclical', 'Communication Services']:
                    if 'Lodging' in industry or 'Travel' in industry: sector_multiplier = 0.80 
                    elif 'Internet' in industry or 'Retail' in industry or 'Restaurants' in industry: sector_multiplier = 1.50 
                elif sector == 'Industrials' and roe > 15: sector_multiplier = 1.50 
                elif sector == 'Financial Services' and ticker in ['SBILIFE.NS', 'HDFCLIFE.NS']: sector_multiplier = 0.80 
            
            fair_pe = base_pe * sector_multiplier
            target = eps * fair_pe
            
            # --- 3. SCORING & DYNAMIC FLAGS ---
            val_score = 0.0
            is_data_glitch = False
            
            if is_etf:
                target = price
                distance = 0.0
                val_score = 5.0
                total_buffett_score = 30.0
                status = "📈 ETF - PASSIVE HOLD"
                fair_pe = 0.0
            elif ticker == "ATHERENERG.NS":
                target = price 
                distance = 0.0
                val_score = 3.0
                total_buffett_score = round(min(30.0, quality_score + val_score), 1)
                status = "🚀 PRE-PROFIT EV"
                fair_pe = 0.0
            else:
                if eps > (price * 0.4): 
                    is_data_glitch = True
                    distance = 999
                    target = 0.0
                elif price > 0 and target > 0:
                    distance = ((price - target) / target) * 100
                    if distance <= 0: val_score = 5.0
                    elif distance <= 5: val_score = 4.0
                    elif distance <= 15: val_score = 2.0
                else:
                    distance = 999
                total_buffett_score = round(quality_score + val_score, 1)

                if is_data_glitch: status = "⚠️ API GLITCH"
                elif total_buffett_score < 18.0: status = "☠️ MOAT BROKEN - SELL 100%"
                elif distance >= 150.0: status = "🔥 MANIA - TRIM 30%"
                elif distance >= 100.0: status = "🚨 BUBBLE - TRIM 20%"
                elif distance >= 75.0: status = "🟠 OVERVALUED - TRIM 10%"
                elif distance <= 0: status = "✅ IN BUY ZONE"
                elif distance <= 5: status = "⚠️ NEAR BUY ZONE"
                else: status = "⏳ WAIT"

            if (eps > 0 and price > 0) or is_etf or ticker == "ATHERENERG.NS": 
                all_data.append({
                    "Ticker": ticker, 
                    "Stock": info.get('shortName', ticker),
                    "Live Price": price,
                    "Live EPS": eps,
                    "ROE (%)": round(roe, 1),
                    "Growth (%)": round(growth, 1), 
                    "Numeric Score": total_buffett_score, 
                    "Buffett Score": f"{total_buffett_score}/30",
                    "Fair P/E": round(fair_pe, 1),
                    "Target (₹)": round(target, 0),
                    "Distance (%)": round(distance, 1),
                    "Action": status
                })
        except Exception as e:
            errors.append(f"{ticker}: {str(e)[:50]}")
            continue 
    return all_data, errors

# --- UI EXECUTION ---
st.title("🏛️ Sravan's Unified Command Center v8.4")
st.write("Complete Portfolio OS. Automating execution, rebalancing, and live Equity/Debt asset allocation.")
st.caption(f"Last Market Sync: {pd.Timestamp.now().strftime('%d %b %Y %H:%M IST')}")

if st.button("🚀 Run Command Center Scan"):
    with st.spinner("Fetching batch market data, live NAVs, and calculating broker execution orders..."):
        all_data, errors = fetch_market_data(SCAN_LIST)
        
    if errors:
        st.warning(f"API Disruptions: Failed to fetch {len(errors)} tickers. ({', '.join(errors[:3])}...)")
        
    if all_data:
        df_all = pd.DataFrame(all_data)
        
        # --- REBALANCE ENGINE ---
        df_fortress = df_all[df_all["Ticker"].isin(CORE_PORTFOLIO)].copy()
        df_elite = df_all[df_all["Numeric Score"] >= 20.0].copy()
        
        df_fortress["Qty"] = df_fortress["Ticker"].map(lambda t: CORE_HOLDINGS.get(t, {}).get("Qty", 0))
        df_fortress["Current Value (₹)"] = df_fortress["Qty"] * df_fortress["Live Price"]
        total_fortress_value = df_fortress["Current Value (₹)"].sum()
        
        if total_fortress_value > 0:
            df_fortress["Actual Wt (%)"] = (df_fortress["Current Value (₹)"] / total_fortress_value) * 100
        else:
            df_fortress["Actual Wt (%)"] = 100 / len(CORE_PORTFOLIO)
            
        total_quality = df_fortress["Numeric Score"].sum()
        df_fortress["Target Wt (%)"] = (df_fortress["Numeric Score"] / total_quality) * 100
        df_fortress["Deviation (%)"] = df_fortress["Actual Wt (%)"] - df_fortress["Target Wt (%)"]
        
        df_sip = df_fortress[df_fortress["Action"].isin(["✅ IN BUY ZONE", "⚠️ NEAR BUY ZONE"])].copy()
        total_executed_value = 0.0
        dry_powder_generated = sip_capital

        if not df_sip.empty:
            df_sip["Val_Weight"] = df_sip["Numeric Score"] * (1 - (df_sip["Distance (%)"].astype(float) / 100))
            df_sip["Reb_Mult"] = (df_sip["Target Wt (%)"] / df_sip["Actual Wt (%)"].clip(lower=1.0)).clip(0.1, 3.0)
            df_sip["Final_Weight"] = df_sip["Val_Weight"] * df_sip["Reb_Mult"]
            total_weight = df_sip["Final_Weight"].sum()
            
            if total_weight > 0:
                df_sip["Raw_Allocation"] = (df_sip["Final_Weight"] / total_weight) * sip_capital
                max_alloc = sip_capital * 0.50
                df_sip["Raw_Allocation"] = df_sip["Raw_Allocation"].clip(upper=max_alloc)
            else:
                df_sip["Raw_Allocation"] = sip_capital / len(df_sip)

            df_sip["Shares to Buy"] = (df_sip["Raw_Allocation"] // df_sip["Live Price"]).astype(int)
            df_sip["Executed (₹)"] = df_sip["Shares to Buy"] * df_sip["Live Price"]
            df_sip = df_sip.drop(columns=["Val_Weight", "Reb_Mult", "Final_Weight", "Raw_Allocation"]) 
            total_executed_value = df_sip["Executed (₹)"].sum()
            dry_powder_generated = sip_capital - total_executed_value

        # --- FAMILY PORTFOLIO ---
        df_family = df_all[df_all["Ticker"].isin(FAMILY_PORTFOLIO.keys())].copy()
        total_current = 0
        total_pnl_pct = 0.0
        
        if not df_family.empty:
            df_family["Qty"] = df_family["Ticker"].map(lambda t: FAMILY_PORTFOLIO[t]["Qty"])
            df_family["Entry Price"] = df_family["Ticker"].map(lambda t: FAMILY_PORTFOLIO[t]["Entry Price"])
            df_family["Invested"] = df_family["Qty"] * df_family["Entry Price"]
            df_family["Current Value"] = df_family["Qty"] * df_family["Live Price"]
            df_family["P&L (%)"] = ((df_family["Live Price"] - df_family["Entry Price"]) / df_family["Entry Price"]) * 100
            total_invested = df_family["Invested"].sum()
            total_current = df_family["Current Value"].sum()
            total_pnl_pct = ((total_current - total_invested) / total_invested) * 100 if total_invested > 0 else 0.0

        # --- LIVE NAV FETCHER FOR DEBT ---
        total_debt_value = 0.0
        debt_display_data = [] 
        
        for fund_name, data in DEBT_HOLDINGS.items():
            live_nav = data.get("Fallback_NAV", 0.0)
            ticker = data.get("Ticker", "")
            
            if ticker:
                try:
                    mf_ticker = yf.Ticker(ticker)
                    fetched_nav = mf_ticker.fast_info.get('lastPrice')
                    if fetched_nav and fetched_nav > 0:
                        live_nav = fetched_nav
                except Exception:
                    pass 
            
            fund_value = data.get("Qty", 0.0) * live_nav
            total_debt_value += fund_value
            debt_display_data.append(f"{fund_name} (Live NAV: ₹{live_nav:.2f})")

        # --- EXECUTIVE PORTFOLIO SUMMARY CARD ---
        st.markdown("---")
        st.subheader("📊 Executive Portfolio Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        if not df_family.empty: col1.metric("Family Portfolio Value", f"₹{total_current:,.0f}", f"{total_pnl_pct:+.2f}%")
        else: col1.metric("Family Portfolio Value", "N/A")
            
        buy_zone_count = len(df_sip)
        delta_str = f"{buy_zone_count} in Buy Zone" if buy_zone_count > 0 else "None in Buy Zone"
        col2.metric("Core Fortress Status", f"{buy_zone_count} / {len(CORE_PORTFOLIO)}", delta_str, delta_color="off")
        
        if buy_zone_count > 0: col3.metric("Executed Capital", f"₹{total_executed_value:,.0f}", f"₹{dry_powder_generated:,.0f} to Liquid Fund", delta_color="normal")
        else: col3.metric("Capital Deployment", "HOLD CASH", "Dry Powder / Liquid Funds", delta_color="inverse")
            
        elite_count = len(df_elite)
        col4.metric("Elite Discoveries", f"{elite_count} Stocks", "Scoring >= 20/30", delta_color="off")

        # --- TIER 0: TOTAL NET WORTH ASSET ALLOCATION (RESTRICTED TO CORE + DEBT) ---
        st.markdown("---")
        st.subheader("🥧 Core Net Worth: Equity vs. Debt")
        
        # Calculate Net Worth tracking ONLY Core 6 + Debt (Excluding Family)
        core_net_worth = total_fortress_value + total_debt_value
        
        col_pie, col_stats = st.columns([1.5, 1])
        
        with col_stats:
            st.write("<br><br>", unsafe_allow_html=True) 
            st.metric("Total Core Assets (Fortress + Debt)", f"₹{core_net_worth:,.0f}")
            
            if core_net_worth > 0:
                equity_ratio = (total_fortress_value / core_net_worth) * 100
                debt_ratio = (total_debt_value / core_net_worth) * 100
                st.write(f"📈 **Core Equity:** {equity_ratio:.1f}%")
                st.write(f"🛡️ **Strategic Debt:** {debt_ratio:.1f}%")
                
                for text in debt_display_data:
                    st.caption(f"✓ Tracking: {text}")
                
                st.caption("This visualization excludes your family portfolio. It reflects your personal strategic balance between the Elite 6 and your Dry Powder war chest.")

        with col_pie:
            pie_labels = list(df_fortress["Stock"])
            pie_sizes = list(df_fortress["Current Value (₹)"])
            
            labels_sizes = [(l, s) for l, s in zip(pie_labels, pie_sizes) if s > 0]
            if total_debt_value > 0:
                labels_sizes.append(("Kotak Arbitrage Fund", total_debt_value))
                
            if labels_sizes:
                labels, sizes = zip(*labels_sizes)
                fig, ax = plt.subplots(figsize=(6, 6))
                
                wedges, texts, autotexts = ax.pie(
                    sizes, labels=labels, autopct='%1.1f%%',
                    startangle=140,
                    wedgeprops={'edgecolor': 'white', 'linewidth': 1}
                )
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_weight('bold')
                    
                ax.axis('equal')
                st.pyplot(fig)

        # --- TIER 1: THE UNIFIED SIP EXECUTION ALGORITHM ---
        st.markdown("---")
        st.subheader(f"💰 Unified Execution Desk (Target: ₹{sip_capital:,.0f})")
        st.caption("🧠 **The Math:** The algorithm calculates the ideal portfolio balance and converts it directly into whole, executable shares.")
        
        if not df_sip.empty:
            df_active_orders = df_sip[df_sip["Shares to Buy"] > 0]
            
            if not df_active_orders.empty:
                cols_to_show = ["Stock", "Live Price", "Target (₹)", "Distance (%)", "Actual Wt (%)", "Target Wt (%)", "Deviation (%)", "Buffett Score", "Shares to Buy", "Executed (₹)", "Action"]
                df_sip_disp = format_df(df_active_orders, drop_score=True)[cols_to_show]
                st.dataframe(df_sip_disp.style.apply(highlight_action, axis=1), use_container_width=True)
                
                st.success(f"📈 **Execution Strategy:** Buy the exact equity shares listed above. Sweep the remaining **₹{dry_powder_generated:,.2f}** directly into your **Kotak Arbitrage Fund**.")
            else:
                 st.info("The engine calculated the ideal distribution, but your capital wasn't enough to buy a full share of the recommended stocks this month. Sweep all capital to the Kotak Arbitrage Fund.")
        else:
            st.success("All core stocks are currently overvalued. Execute your Dry Powder Strategy (Kotak Arbitrage Fund) entirely this month.")

        # --- TIER 2: 6-STOCK FORTRESS RADAR ---
        st.markdown("---")
        st.subheader("🛡️ The 6-Stock Fortress Radar")
        st.write("Complete structural overview of your core holdings, weights, and fundamental health.")
        cols_fortress = ["Stock", "Qty", "Current Value (₹)", "Actual Wt (%)", "Target Wt (%)", "Deviation (%)", "Live Price", "Target (₹)", "Distance (%)", "Buffett Score", "Action"]
        df_fortress_disp = format_df(df_fortress)[cols_fortress]
        st.dataframe(df_fortress_disp.style.apply(highlight_action, axis=1), use_container_width=True)
        
        # --- TIER 3: FAMILY PORTFOLIOS ---
        st.markdown("---")
        st.subheader("👨‍👩‍👦 Family Portfolios (Son & Wife)")
        st.write("Special tracking dashboard displaying real-time P&L along with core fundamental metrics.")
        
        if not df_family.empty:
            cols_order = ["Stock", "Qty", "Entry Price", "Live Price", "Invested", "Current Value", "P&L (%)", "Buffett Score", "Growth (%)", "Fair P/E", "Target (₹)", "Distance (%)", "Action"]
            df_family_disp = df_family[cols_order].sort_values(by="P&L (%)", ascending=False).reset_index(drop=True)
            
            df_family_disp["Entry Price"] = df_family_disp["Entry Price"].apply(lambda x: f"₹{x:,.2f}")
            df_family_disp["Live Price"] = df_family_disp["Live Price"].apply(lambda x: f"₹{x:,.2f}")
            df_family_disp["Invested"] = df_family_disp["Invested"].apply(lambda x: f"₹{x:,.0f}")
            df_family_disp["Current Value"] = df_family_disp["Current Value"].apply(lambda x: f"₹{x:,.0f}")
            df_family_disp["P&L (%)"] = df_family_disp["P&L (%)"].apply(lambda x: f"{x:+.2f}%")
            df_family_disp["Growth (%)"] = df_family_disp["Growth (%)"].apply(lambda x: f"{x}%")
            df_family_disp["Fair P/E"] = df_family_disp.apply(lambda row: "N/A" if row["Fair P/E"] == 0 else row["Fair P/E"], axis=1)
            df_family_disp["Target (₹)"] = df_family_disp.apply(lambda row: "N/A" if ("ETF" in row["Action"] or "PRE-PROFIT" in row["Action"]) else f"₹{row['Target (₹)']:,.0f}", axis=1)
            df_family_disp["Distance (%)"] = df_family_disp.apply(lambda row: "N/A" if ("ETF" in row["Action"] or "PRE-PROFIT" in row["Action"]) else f"{row['Distance (%)']}%", axis=1)

            st.dataframe(df_family_disp.style.apply(highlight_family, axis=1), use_container_width=True)
        else:
            st.info("Family portfolio data is currently loading or unavailable.")

        # --- TIER 4: ELITE NIFTY 50 DISCOVERY ---
        st.markdown("---")
        st.subheader("🦅 Elite Discovery Zone (Noise Filtered)")
        st.write("Broader market scan showing only the purest, non-cyclical compounders scoring >= 20/30.")
        
        if not df_elite.empty:
            st.dataframe(format_df(df_elite).style.apply(highlight_action, axis=1), use_container_width=True)
        else:
            st.info("No discovery stocks met the strict >= 20/30 quality threshold today. The broader market is currently lacking high-quality compounders at reasonable metrics.")

        # --- EXPORT MODULE ---
        st.markdown("---")
        st.subheader("💾 Export Data")
        csv_data = df_all.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full Scan Data (CSV)",
            data=csv_data,
            file_name=f"QGARP_Scan_{pd.Timestamp.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )

    else:
        st.error("Data fetch failed. Market data is temporarily restricted. Please try again later.")
