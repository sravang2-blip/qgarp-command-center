import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import time

st.set_page_config(page_title="Sravan's QGARP Command Center v11.4", layout="wide")

# --- PERSISTENT CONFIGURATION MANAGEMENT ---
CONFIG_FILE = "portfolio_config.json"

DEFAULT_CONFIG = {
    "CORE_HOLDINGS": {
        "ASIANPAINT.NS": {"Qty": 12}, 
        "NESTLEIND.NS": {"Qty": 24}, 
        "PIDILITIND.NS": {"Qty": 21}, 
        "HDFCBANK.NS": {"Qty": 34}, 
        "TCS.NS": {"Qty": 12}, 
        "ITC.NS": {"Qty": 98}
    },
    "DEBT_HOLDINGS": {
        "Kotak Arbitrage Fund": {"Ticker": "0P0000XV5S.BO", "Qty": 80.86, "Fallback_NAV": 34.00} 
    },
    "FAMILY_PORTFOLIO": {
        "ATHERENERG.NS": {"Qty": 250, "Entry Price": 425.60},     
        "IREDA.NS": {"Qty": 480, "Entry Price": 141.37},     
        "KPIGREEN.NS": {"Qty": 93, "Entry Price": 486.57},   
        "SUZLON.NS": {"Qty": 302, "Entry Price": 46.52},     
        "KEC.NS": {"Qty": 78, "Entry Price": 589.67},        
        "JUNIORBEES.NS": {"Qty": 35, "Entry Price": 722.99}, 
        "HDFCSML250.NS": {"Qty": 157, "Entry Price": 156.25} 
    }
}

# --- V11.2: STATEFUL LEDGER MIGRATION ---
def migrate_ledger(config):
    default_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    for category in ["CORE_HOLDINGS", "FAMILY_PORTFOLIO"]:
        if category in config:
            for ticker, data in config[category].items():
                if "Lifetime_Dividends" not in data:
                    data["Lifetime_Dividends"] = 0.0
                if "Last_Dividend_Date" not in data:
                    data["Last_Dividend_Date"] = default_date
    return config

def load_config():
    if not os.path.exists(CONFIG_FILE):
        config = DEFAULT_CONFIG
    else:
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except (json.JSONDecodeError, KeyError):
            st.warning("⚠️ Local configuration file corrupted or unreadable. Safely reverting to default parameters.")
            config = DEFAULT_CONFIG
            
    return migrate_ledger(config)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

app_config = load_config()
CORE_HOLDINGS = app_config.get("CORE_HOLDINGS", DEFAULT_CONFIG["CORE_HOLDINGS"])
DEBT_HOLDINGS = app_config.get("DEBT_HOLDINGS", DEFAULT_CONFIG["DEBT_HOLDINGS"])
FAMILY_PORTFOLIO = app_config.get("FAMILY_PORTFOLIO", DEFAULT_CONFIG["FAMILY_PORTFOLIO"])
CORE_PORTFOLIO = list(CORE_HOLDINGS.keys())

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

with st.sidebar.expander("⚙️ Update Portfolio Quantities", expanded=False):
    with st.form("update_holdings_form"):
        st.write("Update your core shares, family portfolio, and fund units.")
        
        st.markdown("**Core Equity (Shares)**")
        new_core = {}
        for ticker, data in CORE_HOLDINGS.items():
            new_core[ticker] = {
                "Qty": st.number_input(ticker, min_value=0, value=int(data.get("Qty", 0)), step=1),
                "Lifetime_Dividends": data.get("Lifetime_Dividends", 0.0),
                "Last_Dividend_Date": data.get("Last_Dividend_Date", "2026-03-01")
            }
            
        st.markdown("**Family Portfolio (Shares & Entry Price)**")
        new_family = {}
        for ticker, data in FAMILY_PORTFOLIO.items():
            col1, col2 = st.columns(2)
            with col1:
                f_qty = st.number_input(f"{ticker} Qty", min_value=0, value=int(data.get("Qty", 0)), step=1)
            with col2:
                f_price = st.number_input(f"{ticker} Price", min_value=0.0, value=float(data.get("Entry Price", 0.0)), format="%.2f")
            new_family[ticker] = {
                "Qty": f_qty, 
                "Entry Price": f_price,
                "Lifetime_Dividends": data.get("Lifetime_Dividends", 0.0),
                "Last_Dividend_Date": data.get("Last_Dividend_Date", "2026-03-01")
            }

        st.markdown("**Dry Powder (Units)**")
        new_debt = {}
        for fund, data in DEBT_HOLDINGS.items():
            new_debt[fund] = {
                "Ticker": data["Ticker"],
                "Qty": st.number_input(fund, min_value=0.0, value=float(data.get("Qty", 0.0)), step=1.0, format="%.3f"),
                "Fallback_NAV": data.get("Fallback_NAV", 34.0)
            }
            
        if st.form_submit_button("💾 Save Changes to Disk"):
            app_config["CORE_HOLDINGS"] = new_core
            app_config["FAMILY_PORTFOLIO"] = new_family
            app_config["DEBT_HOLDINGS"] = new_debt
            save_config(app_config)
            st.success("Holdings & Ledgers saved securely!")
            st.rerun()

st.sidebar.caption("v11.4 Engine: The Final Masterpiece. UI Polish & Accounting Complete.")

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
    if "Numeric Score" in df.columns:
        df = df.sort_values(by="Numeric Score", ascending=False)
        
    cols_to_drop = ["Ticker"]
    if drop_score and "Numeric Score" in df.columns:
        cols_to_drop.append("Numeric Score")
        
    df_disp = df.drop(columns=[col for col in cols_to_drop if col in df.columns]).reset_index(drop=True)
    
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

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market_data(scan_list_param):
    all_data = []
    errors = []
    
    tickers_string = " ".join(scan_list_param)
    tickers_obj = yf.Tickers(tickers_string)
    
    for i, ticker in enumerate(scan_list_param):
        time.sleep(0.05) 
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
            debt_eq = raw_debt / 100 
            
            growth = safe_float(info, 'earningsGrowth', 0.0) * 100
            if growth == 0: growth = safe_float(info, 'revenueGrowth', 0.0) * 100
            fcf = safe_float(info, 'freeCashflow', 0.0)
            sector = info.get('sector', '')
            industry = info.get('industry', '')

            moat_score = min(10.0, max(0.0, (roe / 4) + (profit_margin / 4)))
            
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
            
            is_boosted = False
            if ticker == "KEC.NS" and profit_margin < 8.0: 
                quality_score += 8.0; is_boosted = True  
            elif ticker in ["IREDA.NS", "KPIGREEN.NS"] and roe < 20.0: 
                quality_score += 2.0; is_boosted = True  
            elif ticker == "ATHERENERG.NS" and eps <= 0: 
                quality_score += 5.0; is_boosted = True  
            elif ticker == "SUZLON.NS" and debt_eq > 0.1: 
                quality_score += 1.0; is_boosted = True  
                
            quality_score = min(25.0, quality_score)
            base_pe = 10 + (quality_score * 1.0)
            
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

            if is_boosted:
                status += " ⚡ BOOSTED"

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
            errors.append(f"{ticker}: {str(e)}")
            continue 
    return all_data, errors

# --- UI EXECUTION ---
st.title("🏛️ Sravan's Unified Command Center v11.4")
st.write("Complete Portfolio OS. Automating execution, rebalancing, and stateful dividend harvesting.")
st.caption(f"Last Market Sync: {pd.Timestamp.now().strftime('%d %b %Y %H:%M IST')}")

if st.button("🚀 Run Command Center Scan"):
    with st.spinner("Scanning markets, updating your Stateful Ledger, and routing orders..."):
        
        # --- V11.2 STATEFUL DIVIDEND LEDGER MODULE ---
        config_changed = False
        total_dividend_cash_30d = 0.0
        
        for category in ["CORE_HOLDINGS", "FAMILY_PORTFOLIO"]:
            for ticker, data in app_config[category].items():
                qty = data.get("Qty", 0)
                if qty <= 0: continue
                
                try:
                    time.sleep(0.05)
                    divs = yf.Ticker(ticker).dividends
                    if not divs.empty:
                        divs.index = divs.index.tz_localize(None)
                        
                        cutoff_30d = pd.Timestamp.now().tz_localize(None) - pd.Timedelta(days=30)
                        recent_divs = divs[divs.index >= cutoff_30d]
                        total_dividend_cash_30d += float(recent_divs.sum()) * qty
                        
                        last_date_str = data.get("Last_Dividend_Date", "1970-01-01")
                        last_date = pd.Timestamp(last_date_str).tz_localize(None)
                        
                        new_divs = divs[divs.index > last_date]
                        if not new_divs.empty:
                            new_cash = float(new_divs.sum()) * qty
                            app_config[category][ticker]["Lifetime_Dividends"] += new_cash
                            app_config[category][ticker]["Last_Dividend_Date"] = new_divs.index.max().strftime('%Y-%m-%d')
                            config_changed = True
                except Exception:
                    pass
        
        if config_changed:
            save_config(app_config)
            
        total_deployment_capital = sip_capital + total_dividend_cash_30d

        all_data, errors = fetch_market_data(SCAN_LIST)
        
    if errors:
        st.warning(f"API Disruptions: Failed to fetch {len(errors)} tickers.")
        with st.expander("View Detailed API Error Logs"):
            for err in errors:
                st.write(err)
        
    if all_data:
        df_all = pd.DataFrame(all_data)
        
        df_fortress = df_all[df_all["Ticker"].isin(CORE_PORTFOLIO)].copy()
        
        nifty_discovery_pool = [t for t in NIFTY_TICKERS if t not in EXCLUDE_LIST]
        df_elite = df_all[(df_all["Numeric Score"] >= 20.0) & (df_all["Ticker"].isin(nifty_discovery_pool))].copy()
        
        df_fortress["Qty"] = df_fortress["Ticker"].map(lambda t: CORE_HOLDINGS.get(t, {}).get("Qty", 0))
        df_fortress["Current Value (₹)"] = df_fortress["Qty"] * df_fortress["Live Price"]
        
        df_fortress["Lifetime Div (₹)"] = df_fortress["Ticker"].map(lambda t: app_config["CORE_HOLDINGS"].get(t, {}).get("Lifetime_Dividends", 0.0))
        df_fortress["Lifetime Div (₹)"] = df_fortress["Lifetime Div (₹)"].apply(lambda x: f"₹{x:,.0f}")

        total_fortress_value = df_fortress["Current Value (₹)"].sum()
        
        if total_fortress_value > 0:
            df_fortress["Actual Wt (%)"] = (df_fortress["Current Value (₹)"] / total_fortress_value) * 100
        else:
            df_fortress["Actual Wt (%)"] = 100 / len(CORE_PORTFOLIO)
            
        total_quality = df_fortress["Numeric Score"].sum()
        df_fortress["Target Wt (%)"] = (df_fortress["Numeric Score"] / total_quality) * 100
        df_fortress["Deviation (%)"] = df_fortress["Actual Wt (%)"] - df_fortress["Target Wt (%)"]
        
        df_sip = df_fortress[
            (df_fortress["Action"].str.contains("✅ IN BUY ZONE|⚠️ NEAR BUY ZONE", regex=True, na=False)) & 
            (df_fortress["Live Price"] > 0)
        ].copy()
        
        total_executed_value = 0.0
        dry_powder_generated = total_deployment_capital

        if not df_sip.empty:
            capped_distance = df_sip["Distance (%)"].astype(float).clip(lower=-30.0)
            df_sip["Val_Weight"] = df_sip["Numeric Score"] * (1 - (capped_distance / 100))
            
            df_sip["Reb_Mult"] = (df_sip["Target Wt (%)"] / df_sip["Actual Wt (%)"].clip(lower=1.0)).clip(0.1, 3.0)
            df_sip["Final_Weight"] = df_sip["Val_Weight"] * df_sip["Reb_Mult"]
            total_weight = df_sip["Final_Weight"].sum()
            
            if total_weight > 0:
                df_sip["Raw_Allocation"] = (df_sip["Final_Weight"] / total_weight) * total_deployment_capital
                max_alloc = total_deployment_capital * 0.50
                df_sip["Raw_Allocation"] = df_sip["Raw_Allocation"].clip(upper=max_alloc)
            else:
                df_sip["Raw_Allocation"] = total_deployment_capital / len(df_sip)

            df_sip["Shares to Buy"] = (df_sip["Raw_Allocation"] // df_sip["Live Price"]).astype(int)
            df_sip["Executed (₹)"] = df_sip["Shares to Buy"] * df_sip["Live Price"]
            df_sip = df_sip.drop(columns=["Val_Weight", "Reb_Mult", "Final_Weight", "Raw_Allocation"]) 
            total_executed_value = df_sip["Executed (₹)"].sum()
            dry_powder_generated = total_deployment_capital - total_executed_value

        df_family = df_all[df_all["Ticker"].isin(FAMILY_PORTFOLIO.keys())].copy()
        total_current = 0
        total_pnl_pct = 0.0
        
        if not df_family.empty:
            df_family["Qty"] = df_family["Ticker"].map(lambda t: FAMILY_PORTFOLIO[t]["Qty"])
            df_family["Entry Price"] = df_family["Ticker"].map(lambda t: FAMILY_PORTFOLIO[t]["Entry Price"])
            df_family["Invested"] = df_family["Qty"] * df_family["Entry Price"]
            df_family["Current Value"] = df_family["Qty"] * df_family["Live Price"]
            df_family["P&L (%)"] = ((df_family["Live Price"] - df_family["Entry Price"]) / df_family["Entry Price"]) * 100
            
            df_family["Lifetime Div (₹)"] = df_family["Ticker"].map(lambda t: app_config["FAMILY_PORTFOLIO"].get(t, {}).get("Lifetime_Dividends", 0.0))
            df_family["Lifetime Div (₹)"] = df_family["Lifetime Div (₹)"].apply(lambda x: f"₹{x:,.0f}")

            total_invested = df_family["Invested"].sum()
            total_current = df_family["Current Value"].sum()
            total_pnl_pct = ((total_current - total_invested) / total_invested) * 100 if total_invested > 0 else 0.0

        # --- V11.3/4: DEBT TRACKING MODULE ---
        total_debt_value = 0.0
        debt_display_data = [] 
        debt_table_data = []
        
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
            
            qty = data.get("Qty", 0.0)
            fund_value = qty * live_nav
            total_debt_value += fund_value
            debt_display_data.append(f"{fund_name} (Live NAV: ₹{live_nav:.2f})")
            
            debt_table_data.append({
                "Fund Name": fund_name,
                "Ticker": ticker if ticker else "N/A",
                "Units Accumulated": qty,
                "Live NAV (₹)": live_nav,
                "Total Corpus (₹)": fund_value
            })
            
        df_debt = pd.DataFrame(debt_table_data)

        st.markdown("---")
        st.subheader("📊 Executive Portfolio Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        if not df_family.empty: col1.metric("Family Portfolio", f"₹{total_current:,.0f}", f"{total_pnl_pct:+.2f}%")
        else: col1.metric("Family Portfolio", "N/A")
            
        buy_zone_count = len(df_sip)
        delta_str = f"{buy_zone_count} in Buy Zone" if buy_zone_count > 0 else "None in Buy Zone"
        col2.metric("Fortress Status", f"{buy_zone_count} / {len(CORE_PORTFOLIO)}", delta_str, delta_color="off")
        
        if buy_zone_count > 0: col3.metric("Capital Deployed", f"₹{total_executed_value:,.0f}", f"₹{dry_powder_generated:,.0f} to Arbitrage", delta_color="normal")
        else: col3.metric("Capital Deployed", "HOLD CASH", "All to Arbitrage", delta_color="inverse")
            
        if total_dividend_cash_30d > 0: col4.metric("Dividend Harvest (30D)", f"₹{total_dividend_cash_30d:,.0f}", "Reinvested", delta_color="normal")
        else: col4.metric("Dividend Harvest (30D)", "₹0", "Awaiting Ex-Dates", delta_color="off")
            
        elite_count = len(df_elite)
        col5.metric("Elite Discoveries", f"{elite_count} Stocks", "Scoring >= 20/30", delta_color="off")

        st.markdown("---")
        st.subheader("🥧 Core Net Worth: Equity vs. Debt")
        
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

        st.markdown("---")
        st.subheader(f"💰 Unified Execution Desk (Target Capital: ₹{total_deployment_capital:,.0f})")
        st.caption("🧠 **The Math:** The algorithm calculates the ideal portfolio balance and converts it directly into whole, executable shares.")
        
        if not df_sip.empty:
            df_active_orders = df_sip[df_sip["Shares to Buy"] > 0]
            
            if not df_active_orders.empty:
                cols_to_show = ["Stock", "Live Price", "Target (₹)", "Distance (%)", "Actual Wt (%)", "Target Wt (%)", "Deviation (%)", "Buffett Score", "Shares to Buy", "Executed (₹)", "Action"]
                df_sip_disp = format_df(df_active_orders, drop_score=True)[cols_to_show]
                st.dataframe(df_sip_disp.style.apply(highlight_action, axis=1), use_container_width=True)
                
                if total_dividend_cash_30d > 0:
                    st.success(f"📈 **Execution Strategy:** Buy the exact equity shares listed above. | **Total Executed:** ₹{total_executed_value:,.0f} | **Dry Powder to Kotak Arbitrage:** ₹{dry_powder_generated:,.0f} (includes ₹{total_dividend_cash_30d:,.0f} dividends)")
                else:
                    st.success(f"📈 **Execution Strategy:** Buy the exact equity shares listed above. | **Total Executed:** ₹{total_executed_value:,.0f} | **Dry Powder to Kotak Arbitrage:** ₹{dry_powder_generated:,.0f}")
            else:
                 st.info("The engine calculated the ideal distribution, but your capital wasn't enough to buy a full share of the recommended stocks this month. Sweep all capital to the Kotak Arbitrage Fund.")
        else:
            if total_dividend_cash_30d > 0:
                st.success(f"All core stocks are currently overvalued. Execute your Dry Powder Strategy (Kotak Arbitrage Fund) entirely this month. | **Total Executed:** ₹0 | **Dry Powder to Kotak Arbitrage:** ₹{dry_powder_generated:,.0f} (includes ₹{total_dividend_cash_30d:,.0f} dividends)")
            else:
                st.success(f"All core stocks are currently overvalued. Execute your Dry Powder Strategy (Kotak Arbitrage Fund) entirely this month. | **Total Executed:** ₹0 | **Dry Powder to Kotak Arbitrage:** ₹{dry_powder_generated:,.0f}")

        st.markdown("---")
        st.subheader("🛡️ The 6-Stock Fortress Radar")
        st.write("Complete structural overview of your core holdings, weights, and fundamental health.")
        cols_fortress = ["Stock", "Qty", "Current Value (₹)", "Actual Wt (%)", "Target Wt (%)", "Deviation (%)", "Live Price", "Target (₹)", "Distance (%)", "Buffett Score", "Lifetime Div (₹)", "Action"]
        df_fortress_disp = format_df(df_fortress)[cols_fortress]
        st.dataframe(df_fortress_disp.style.apply(highlight_action, axis=1), use_container_width=True)
        
        st.markdown("---")
        st.subheader("👨‍👩‍👦 Family Portfolios (Son & Wife)")
        st.write("Special tracking dashboard displaying real-time P&L along with core fundamental metrics.")
        
        if not df_family.empty:
            cols_order = ["Stock", "Qty", "Entry Price", "Live Price", "Invested", "Current Value", "P&L (%)", "Buffett Score", "Growth (%)", "Fair P/E", "Target (₹)", "Distance (%)", "Lifetime Div (₹)", "Action"]
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

        # --- V11.4: STRATEGIC DEBT DASHBOARD (POLISHED) ---
        st.markdown("---")
        st.subheader("🏦 Strategic Debt & Dry Powder")
        st.write("Tracking your risk-free accumulated arbitrage corpus.")
        st.caption("This is your risk-free dry powder. All un-deployed SIP + dividend cash is automatically swept here.")
        if not df_debt.empty:
            df_debt_disp = df_debt.copy()
            df_debt_disp["Units Accumulated"] = df_debt_disp["Units Accumulated"].apply(lambda x: f"{x:,.3f}")
            df_debt_disp["Live NAV (₹)"] = df_debt_disp["Live NAV (₹)"].apply(lambda x: f"₹{x:,.4f}")
            df_debt_disp["Total Corpus (₹)"] = df_debt_disp["Total Corpus (₹)"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(df_debt_disp, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🦅 Elite Discovery Zone (Pure Nifty 50 Screener)")
        st.write("Broader market scan ranking all Nifty 50 compounders scoring >= 20/30, including your existing holdings.")
        
        if not df_elite.empty:
            st.dataframe(format_df(df_elite).style.apply(highlight_action, axis=1), use_container_width=True)
        else:
            st.info("No discovery stocks met the strict >= 20/30 quality threshold today. The broader market is currently lacking high-quality compounders at reasonable metrics.")

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
