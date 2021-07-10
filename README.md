# discord-bot
## Setup
### Development environment

Python version 3.9

Install pipenv


```
pipenv install
```

### Environment variables
* Copy `.env.template` and save it as `.env`
* `TEST_CHANNEL_ID` and `TOKEN` will be available after you set up your discord server and bot application

### Discord
* Create a discord server
* Create a test channel 
* Create a new application in https://discord.com/developers 
* Enable the bot scope in `OAuth2` -> `SCOPES`, enable `BOT PERMISSIONS` -> `Administrator`
* Add the bot to your server
* Navigate back to applications, copy the bot TOKEN from SETTINGS -> Bot and paste it into your `.env` file
* Go to your discord server, copy the ID of your test channel and paste it to `.env` file

### Run locally
Execute:

```
python main.py
```

### Contributing
We will gladly accept contributions, but before you start working on something please read 
[CONTRIBUTING.md](docs/CONTRIBUTING.md) first.
