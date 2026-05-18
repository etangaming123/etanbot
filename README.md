# etanbot

Funny Discord bot that can be added to your account and used anywhere within Discord.

> [!NOTE]
> Uptime of this bot is flaky. You are free to selfhost the bot and run it on your own bot account.

> [!WARNING]
> This bot is intended for self use. etangaming123 is not responsible for sensitive data on this bot being leaked.
> *But it's just a Koko Amusement card...*

You can add the bot to your account [here.](https://discord.com/oauth2/authorize?client_id=1505906056222605352) 

## Features

* 8-ball command
* Braincell count (or random number generator)
* Pizoelectric tiles copypasta ("Japan is turning footsteps into electricity! ⚡Using piezoelectric tiles, every step you take generates a small amount of energy. Millions of steps together can power LED lights and displays in busy places like Shibuya Station. A brilliant way to create a sustainable and smart city -- turning movement into clean, renewable energy 🌱💡")
* (unnofficial) Linkage with Koko Amusement Cards (so you can see how much credit you have left, from the comfort of Discord)
* Built in profiles (for fun!)

## Selfhosting

### You will need:

* A Discord bot
* Python (3.0 or above)
* The required Python libraries in `requirements.txt`

### Discord Bot

1. Log on to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new application using the button on the top right.
3. Add a new app icon. This will be the bot's profile picture.
4. Under the Overview tab, click on "Bot", and reset the bot's token. Copy the new token and keep it somewhere, you'll need it later.
5. Go to the Installation tab, and make sure the installation context is set to "User Install". Select "Discord Provided Link" for the Install link, then copy the generated URL.
6. Paste the url into your favourite browser, and add the bot to your account.

### Python Code

Get all the required modules with:
`pip install -r requirements.txt`

Then, create a `config.json` file in the same directory as `main.py` with the following content:

```json
{"token": "Your Discord Bot Token here",
    "poweruserid": "Your Discord User ID here (optional, for owner-only commands)"
}
```

Finally, run the bot with:
`python main.py`

Refresh your Discord client, and press `/` on your keyboard. You should see the bot's commands in the list, and you can start using it!

Do note that the program has to be continuously running for the bot to work. If you close the terminal or stop the program, the bot will go offline and become unusable until you run it again.
