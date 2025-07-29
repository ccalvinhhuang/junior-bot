# Junior Discord Bot

Message me for system prompt and .env :) 

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create a Discord Bot:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the "Bot" section
   - Create a bot and copy the token

3. **Set up environment variables:**
   - Copy `env_example.txt` to `.env`
   - Replace `your_discord_bot_token_here` with your actual bot token

4. **Invite the bot to your server:**
   - Go to OAuth2 > URL Generator in the Developer Portal
   - Select "bot" scope
   - Select "Send Messages" permission
   - Use the generated URL to invite the bot to your server

## Running the Bot

```bash
python bot.py
```
