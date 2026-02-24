import os
import sys
import datetime
import yfinance as yf
import pandas as pd
import requests

def main():
    try:
        bot_token, chat_id = os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID")
        if not bot_token or not chat_id:
            print("Missing BOT_TOKEN or CHAT_ID environment variables.")
            return

        # STEP A - Fetch Data
        try:
            comex_data = yf.download("HG=F", period="90d", interval="1d", progress=False)
            usdinr_data = yf.download("USDINR=X", period="90d", interval="1d", progress=False)
        except Exception:
            comex_data = usdinr_data = pd.DataFrame()

        if comex_data.empty or usdinr_data.empty:
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data={
                "chat_id": chat_id, "text": "⚠️ Data fetch failed. Will retry tomorrow.", "parse_mode": "Markdown"
            })
            sys.exit(0)

        comex_close = comex_data['Close'].squeeze()
        usdinr_close = usdinr_data['Close'].squeeze()

        df = pd.DataFrame(index=comex_close.index)
        df['comex_close'] = comex_close
        df['usdinr_rate'] = usdinr_close
        df.ffill(inplace=True)
        df.dropna(inplace=True)

        if len(df) < 60:
            raise Exception(f"Not enough data points acquired. Needed 60, got {len(df)}")

        prices = df['comex_close'] * df['usdinr_rate'] / 0.453592
        todays_price = prices.iloc[-1]
        yesterdays_price = prices.iloc[-2]
        five_days_ago_price = prices.iloc[-6] if len(prices) >= 6 else prices.iloc[0]
        
        latest_comex, latest_usdinr = df['comex_close'].iloc[-1], df['usdinr_rate'].iloc[-1]
        daily_change = ((todays_price - yesterdays_price) / yesterdays_price) * 100
        weekly_change = ((todays_price - five_days_ago_price) / five_days_ago_price) * 100
        high_30d, low_30d = prices.tail(30).max(), prices.tail(30).min()

        # STEP B - Indicator 1: RSI (14-day)
        delta = prices.diff()
        avg_gain = delta.clip(lower=0).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = (-delta.clip(upper=0)).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        rsi = (100 - (100 / (1 + avg_gain / avg_loss))).iloc[-1]

        if rsi < 30: rsi_label = "Oversold 📉"
        elif rsi < 40: rsi_label = "Approaching Oversold"
        elif rsi <= 60: rsi_label = "Neutral"
        elif rsi <= 70: rsi_label = "Approaching Overbought"
        else: rsi_label = "Overbought 📈"

        # STEP C - Indicator 2: Price vs 30-Day SMA
        sma_30 = prices.rolling(window=30).mean().iloc[-1]
        pct_deviation = ((todays_price - sma_30) / sma_30) * 100

        # STEP D - Indicator 3: 60-Day Percentile
        percentile = round(((prices.tail(60) < todays_price).sum() / 60) * 100)

        # STEP E - Combined Score
        score = 0
        if rsi < 30: score += 2
        elif rsi < 40: score += 1
        elif rsi <= 60: score += 0
        elif rsi <= 70: score -= 1
        else: score -= 2

        if pct_deviation <= -3: score += 1
        elif pct_deviation >= 3: score -= 1

        if percentile <= 25: score += 1
        elif percentile >= 75: score -= 1

        # STEP F - Recommendation
        if score >= 3:
            emoji, rec, action = "🟢", "STRONG BUY", "Excellent buying opportunity! All indicators show copper is undervalued. Buy maximum planned quantity NOW."
        elif score == 2:
            emoji, rec, action = "🟢", "BUY", "Good time to buy. Most indicators suggest prices are below fair value and likely to rise."
        elif score == 1:
            emoji, rec, action = "🟡", "LEAN BUY", "Slightly favorable. Go ahead with planned purchase if needed."
        elif score == 0:
            emoji, rec, action = "🟡", "NEUTRAL", "No strong signal either way. Buy if you need copper, no urgency to time it."
        elif score == -1:
            emoji, rec, action = "🟠", "LEAN WAIT", "Prices slightly elevated. Defer purchase by 3-5 days if possible."
        elif score == -2:
            emoji, rec, action = "🔴", "WAIT", "Prices appear high. Consider waiting 1-2 weeks for a likely pullback."
        else:
            emoji, rec, action = "🔴", "STRONG WAIT", "All indicators say overbought! Defer purchase and wait for correction. Monitor daily."

        # STEP G - Telegram Message
        today_date = datetime.datetime.now().strftime("%d-%b-%Y")
        sign_dev, sign_daily, sign_weekly = ("+" if x > 0 else "" for x in (pct_deviation, daily_change, weekly_change))
        
        msg = f"""🔔 *DAILY COPPER PRICE ALERT*
📅 {today_date}

💰 *Approx. MCX Copper: ₹{todays_price:.2f}/kg*
(COMEX: {latest_comex:.4f} USD/lb | USD/INR: ₹{latest_usdinr:.2f})

📊 *Indicators:*
• RSI (14-day): {rsi:.1f} — {rsi_label}
• vs 30-Day Avg: {sign_dev}{pct_deviation:.1f}% (Avg: ₹{sma_30:.2f}/kg)
• 60-Day Rank: {percentile}th percentile
• Combined Score: {score}/4

{emoji} *RECOMMENDATION: {rec}*
_{action}_

📈 *Price Context:*
• Today vs Yesterday: {sign_daily}{daily_change:.2f}%
• 7-Day Change: {sign_weekly}{weekly_change:.2f}%
• 30-Day Range: ₹{low_30d:.2f} — ₹{high_30d:.2f}/kg

_Note: Based on COMEX copper (99.7% correlated with MCX). Actual MCX price may differ by 1-3%. Indicators are statistical guides, not guarantees._"""

        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}).raise_for_status()
        
    except Exception as e:
        bot_token, chat_id = os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID")
        if bot_token and chat_id:
            try: requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data={"chat_id": chat_id, "text": f"⚠️ Copper Bot Error: {e}. Will retry tomorrow.", "parse_mode": "Markdown"})
            except: pass
        sys.exit(0)

if __name__ == "__main__":
    main()
