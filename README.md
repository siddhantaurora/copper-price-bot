### Copper Price Alert Bot 🔔

Daily Telegram bot that analyzes MCX copper prices and sends buy/wait recommendations for procurement teams.

**How it works:** Every weekday at 7:00 AM IST, this bot fetches COMEX copper futures data (which tracks MCX with 99.7% correlation), calculates three technical indicators (RSI, moving average deviation, and percentile rank), and sends a recommendation to your Telegram.

**Runs on GitHub's servers for free — your computer does NOT need to be on.**

### Setup (one-time, ~10 minutes):

1. **Create Telegram Bot:**
   - Open Telegram, search for `@BotFather`
   - Send `/newbot`, choose a name and username
   - Save the API token it gives you

2. **Get Your Chat ID:**
   - Search for `@userinfobot` in Telegram
   - Send it any message, it replies with your user ID number
   - Save this number

3. **Deploy:**
   - Fork this repository on GitHub
   - Go to your fork's Settings → Secrets and variables → Actions
   - Add secret `BOT_TOKEN` with your Telegram bot token
   - Add secret `CHAT_ID` with your user ID
   - Go to the Actions tab and enable workflows
   - Click "Run workflow" to test immediately

4. **Done!** Bot runs automatically every weekday at 7 AM IST.

### Understanding the Indicators:

- **RSI (Relative Strength Index):** Measures momentum. Below 30 = oversold (price dropped too fast, likely to bounce back up). Above 70 = overbought (price rose too fast, likely to pull back).
- **30-Day Average Deviation:** Is today's price above or below the recent average? More than 3% below = cheap. More than 3% above = expensive.
- **60-Day Percentile:** Where does today's price rank in the last 3 months? 10th percentile means cheaper than 90% of recent prices.

### Changing Alert Time:

Edit the cron schedule in `.github/workflows/daily_alert.yml`. The format is `minute hour * * days` in UTC. IST = UTC + 5:30.

### Troubleshooting:

- Check the Actions tab for run logs
- Verify your secrets are set correctly
- Test your bot token: open `https://api.telegram.org/bot<YOUR_TOKEN>/getMe` in browser — should show bot info
- Trigger manually: Actions tab → "Daily Copper Price Alert" → "Run workflow"
