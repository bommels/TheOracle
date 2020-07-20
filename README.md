### The Oracle - Discord Bot
This open-source Discord bot is used in <a href='https://discord.gg/P2Smr4Y'>The Simulation</a> server.

##### Running the bot
```bash
# Set your tokens and keys in settings.py and rename the file
mv settings/settings.sample.py settings/settings.py

# Run with docker-compose
docker-compose up -d --build
```

##### Todo
- [ ] Remove duplicate code, create general function for formatting and sending discord trade / liquidation notifications.
- [ ] Create websocket manager that auto reconnect on errors.
