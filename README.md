# Rocket Stock Scanner

A free GitHub Actions scanner that:

- Uses Alpaca market data.
- Scans active US equities.
- Filters price to `$2–$50`.
- Requires previous-day volume of at least `300,000`.
- Calculates EMA20, EMA50, RSI, MACD, Relative Volume, support and resistance.
- Ranks setups and sends the best results to Telegram.

## Required GitHub Actions secrets

Create these under:

`Settings → Secrets and variables → Actions`

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_USER_ID`
- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`

## Install

Upload all files into the repository while keeping the same folders.

Delete or disable the old workflow file:

`.github/workflows/bot.yml`

The new workflow is:

`.github/workflows/scanner.yml`

Go to:

`Actions → Rocket Stock Scanner → Run workflow`

## Important limitations

1. Alpaca free market data generally uses IEX, not Full SIP.
2. GitHub Actions is scheduled automation, not an always-on server.
3. Scheduled runs may be delayed.
4. Telegram commands such as `/analyze` require a persistent server; this version only sends outbound reports.
5. Sharia compliance is not automatically verified.
6. The calculated entry, stop and targets are mechanical estimates, not financial advice.
