import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Sravan's QGARP Command Center", layout="wide")
st.title("🏛️ Sravan's 3-Tier QGARP Command Center")
st.write("Execution at the top, portfolio health in the middle, and pure, noise-free market discovery at the bottom.")

# 🛡️ THE FORTRESS (Never to be altered)
core_portfolio = [
    "ASIANPAINT.NS", "NESTLEIND.NS", "PIDILITIND.NS", "HDFCBANK.NS", "TCS.NS", "ITC.NS"
]

# 👨‍👩‍👦 FAMILY PORTFOLIOS (Son & Wife)
family_portfolio = {
    "ATHERENERG.NS": {"Qty": 250, "Entry Price": 425.60},     
    "IREDA.NS": {"Qty": 480, "Entry Price": 141.37},     
    "KPIGREEN.NS": {"Qty": 93, "Entry Price": 486.57},   
    "SUZLON.NS": {"Qty": 302, "Entry Price": 46.52},     
    "KEC.NS": {"Qty": 78, "Entry Price": 589.67},        
    "JUNIORBEES.NS": {"Qty": 35, "Entry Price": 722.99}, 
    "HDFCSML250.NS": {"Qty": 157, "Entry Price": 156.25} 
}

# The NIFTY 50 Index 
nifty_tickers = [
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

# 🚫 THE QUALITATIVE KILL LIST 
exclude_list = [
    "COALINDIA.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BPCL.NS", "SBIN.NS", 
    "TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", 
    "TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", 
    "ADANIENT.NS", "ADANIPORTS.NS" 
]

scan_list = core_portfolio + list(family_portfolio.keys()) + [t for t in nifty_tickers if t not in core_portfolio and t not in family_portfolio.keys() and t not in exclude_list]

def safe_float(info_dict, key, default=0.0):
    try:
        val = info_dict.get(key)
        if val is None or str(val).strip().upper() in ['N/A', '-', 'NAN', '']:
            return float(default)
        return float(str(val).replace(',', '').replace('%', ''))
    except (ValueError, TypeError):
        return float(default)

if st.button("🚀 Run Command Center Scan"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_data = []
    
    for i, ticker in enumerate(scan_list):
        status_text.text(f"Analyzing {ticker}... ({i+1}/{len(scan_list)})")
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Fast info fallback for current price if primary info fails
            if not info or ('currentPrice' not in info and 'regularMarketPrice' not in info):
                last_price = stock.fast_info.get('lastPrice', 0.0)
                if last_price > 0:
                    info['currentPrice'] = last_price
                    
            price = safe_float(info, 'currentPrice', safe_float(info, 'regularMarketPrice', 0.0))
            eps = safe_float(info, 'trailingEps', 0.0)
            
            is_etf = ticker in ["JUNIORBEES.NS", "HDFCSML250.NS"]
            
            roe = safe_float(info, 'returnOnEquity', 0.0)
            if roe == 0.0:
                book_value = safe_float(info, 'bookValue', 0.0)
                if book_value > 0 and eps > 0: 
                    roe = eps / book_value
            roe = roe * 100
            
            profit_margin = safe_float(info, 'profitMargins', 0.0)
            if profit_margin == 0.0:
                revenue_per_share = safe_float(info, 'revenuePerShare', 0.0)
                if revenue_per_share > 0 and eps > 0: 
                    profit_margin = eps / revenue_per_share
            profit_margin = profit_margin * 100
            
            debt_eq = safe_float(info, 'debtToEquity', 0.0) / 100
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
                
            quality_score = moat_score + fin_score + cons_score
            
            # --- 1.5. DYNAMIC GROWTH OVERRIDES (Future-Proofed) ---
            if ticker == "KEC.NS" and profit_margin < 8.0:
                quality_score += 8.0  # EPC Order Book Premium (Fades if margins naturally rise > 8%)
            elif ticker in ["IREDA.NS", "KPIGREEN.NS"] and roe < 20.0:
                quality_score += 2.0  
            elif ticker == "ATHERENERG.NS" and eps <= 0:
                quality_score += 5.0  # EV Pre-Profit Forgiveness
            elif ticker == "SUZLON.NS" and debt_eq > 0.1:
                quality_score += 1.0  
                
            quality_score = min(25.0, quality_score) # STRICT CAP: Base PE maxes at 35
                
            base_pe = 10 + (quality_score * 1.0)
            
            # --- 2. MULTIPLIERS & CALIBRATION ---
            if ticker in core_portfolio:
                if ticker == "TCS.NS": sector_multiplier = 0.60
                elif ticker == "HDFCBANK.NS": sector_multiplier = 0.65
                elif ticker == "ITC.NS": sector_multiplier = 0.54
                elif ticker == "NESTLEIND.NS": sector_multiplier = 2.00
                elif ticker in ["ASIANPAINT.NS", "PIDILITIND.NS"]: sector_multiplier = 1.80

            elif ticker in family_portfolio:
                if ticker == "IREDA.NS": sector_multiplier = 0.60
                elif ticker == "KPIGREEN.NS": sector_multiplier = 0.65
                elif ticker == "SUZLON.NS": sector_multiplier = 0.65
                elif ticker == "KEC.NS": sector_multiplier = 0.85
                elif ticker == "ATHERENERG.NS": sector_multiplier = 1.00
                else: sector_multiplier = 1.00 
            
            else:
                if ticker == 'RELIANCE.NS': sector_multiplier = 1.00 
                elif sector == 'Consumer Defensive':
                    if industry == 'Tobacco': sector_multiplier = 0.54
                    elif roe > 50: sector_multiplier = 2.00  
                    elif roe > 15: sector_multiplier = 1.80  
                    else: sector_multiplier = 1.20
                elif sector == 'Consumer Cyclical' or sector == 'Communication Services':
                    if 'Lodging' in industry or 'Travel' in industry: sector_multiplier = 0.80 
                    elif 'Internet' in industry or 'Retail' in industry or 'Restaurants' in industry: sector_multiplier = 1.50 
                    else: sector_multiplier = 1.00 
                elif sector == 'Industrials': sector_multiplier = 1.50 if roe > 15 else 1.00 
                elif sector == 'Financial Services':
                    if ticker in ['SBILIFE.NS', 'HDFCLIFE.NS']: sector_multiplier = 0.80 
                    else: sector_multiplier = 0.55 
                elif sector == 'Technology': sector_multiplier = 0.60  
                elif sector == 'Healthcare': sector_multiplier = 1.20
                else: sector_multiplier = 1.00
                
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

            # Strict Inclusion Logic (Standardized to ATHERENERG.NS)
            if (eps > 0 and price > 0) or is_etf or ticker == "ATHERENERG.NS": 
                all_data.append({
                    "Ticker": ticker, 
                    "Stock": info.get('shortName', ticker),
                    "Live Price": price,
                    "Live EPS": eps,
                    "ROE (%)": round(roe, 1),
                    "Numeric Score": total_buffett_score, 
                    "Buffett Score": f"{total_buffett_score}/30",
                    "Fair P/E": round(fair_pe, 1),
                    "Target (₹)": round(target, 0),
                    "Distance (%)": round(distance, 1),
                    "Action": status
                })
        except Exception as e:
            pass 
            
        progress_bar.progress((i + 1) / len(scan_list))
        time.sleep(0.5)

    status_text.text("Scan Complete!")
    
    if all_data:
        df_all = pd.DataFrame(all_data)
        
        # --- LOGIC SPLITS ---
        df_fortress = df_all[df_all["Ticker"].isin(core_portfolio)].copy()
        df_sip = df_fortress[df_fortress["Action"].isin(["✅ IN BUY ZONE", "⚠️ NEAR BUY ZONE"])].copy()
        df_elite = df_all[df_all["Numeric Score"] >= 20.0].copy()

        def format_df(df):
            if df.empty: return df
            df_disp = df.drop(columns=["Ticker", "Numeric Score"]).sort_values(by="Buffett Score", ascending=False).reset_index(drop=True)
            df_disp["Live Price"] = df_disp["Live Price"].apply(lambda x: f"₹{x:,.2f}")
            df_disp["Live EPS"] = df_disp["Live EPS"].apply(lambda x: "N/A" if x <= 0 else f"₹{x:,.2f}")
            df_disp["Target (₹)"] = df_disp.apply(lambda row: "N/A" if ("ETF" in row["Action"] or "PRE-PROFIT" in row["Action"]) else f"₹{row['Target (₹)']:,.0f}", axis=1)
            df_disp["Distance (%)"] = df_disp.apply(lambda row: "N/A" if ("ETF" in row["Action"] or "PRE-PROFIT" in row["Action"]) else f"{row['Distance (%)']}%", axis=1)
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

        # --- TIER 1: THIS MONTH'S SIP EXECUTION ---
        st.markdown("---")
        st.subheader("💰 This Month's SIP Execution")
        st.write("Deploy ₹5,000 strictly into these core portfolio targets today.")
        if not df_sip.empty:
            st.dataframe(format_df(df_sip).style.apply(highlight_action, axis=1), use_container_width=True)
        else:
            st.success("All core stocks are currently overvalued. Execute your Dry Powder Strategy (Liquid/Arbitrage Fund) this month.")

        # --- TIER 2: 6-STOCK FORTRESS RADAR ---
        st.markdown("---")
        st.subheader("🛡️ The 6-Stock Fortress Radar")
        st.write("Complete fundamental health check and exit strategy monitoring.")
        st.dataframe(format_df(df_fortress).style.apply(highlight_action, axis=1), use_container_width=True)
        
        # --- TIER 3: FAMILY PORTFOLIOS (NEW) ---
        st.markdown("---")
        st.subheader("👨‍👩‍👦 Family Portfolios (Son & Wife)")
        st.write("Special tracking dashboard displaying real-time P&L along with core fundamental metrics.")
        
        df_family = df_all[df_all["Ticker"].isin(family_portfolio.keys())].copy()
        
        if not df_family.empty:
            df_family["Qty"] = df_family["Ticker"].map(lambda t: family_portfolio[t]["Qty"])
            df_family["Entry Price"] = df_family["Ticker"].map(lambda t: family_portfolio[t]["Entry Price"])
            
            df_family["Invested"] = df_family["Qty"] * df_family["Entry Price"]
            df_family["Current Value"] = df_family["Qty"] * df_family["Live Price"]
            df_family["P&L (%)"] = ((df_family["Live Price"] - df_family["Entry Price"]) / df_family["Entry Price"]) * 100
            
            cols_order = ["Stock", "Qty", "Entry Price", "Live Price", "Invested", "Current Value", "P&L (%)", "Buffett Score", "Fair P/E", "Target (₹)", "Distance (%)", "Action"]
            df_family_disp = df_family[cols_order].sort_values(by="P&L (%)", ascending=False).reset_index(drop=True)
            
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
                    if pnl_val > 0:
                        row_styles[pnl_idx] = 'color: #00FF00; font-weight: bold'
                    elif pnl_val < 0:
                        row_styles[pnl_idx] = 'color: #FF0000; font-weight: bold'
                except:
                    pass
                return row_styles

            df_family_disp["Entry Price"] = df_family_disp["Entry Price"].apply(lambda x: f"₹{x:,.2f}")
            df_family_disp["Live Price"] = df_family_disp["Live Price"].apply(lambda x: f"₹{x:,.2f}")
            df_family_disp["Invested"] = df_family_disp["Invested"].apply(lambda x: f"₹{x:,.0f}")
            df_family_disp["Current Value"] = df_family_disp["Current Value"].apply(lambda x: f"₹{x:,.0f}")
            df_family_disp["P&L (%)"] = df_family_disp["P&L (%)"].apply(lambda x: f"{x:+.2f}%")
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
        st.dataframe(format_df(df_elite).style.apply(highlight_action, axis=1), use_container_width=True)

    else:
        st.error("Data fetch failed. Market data is temporarily restricted. Please try again later.")
