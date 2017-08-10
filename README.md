# slack_bot
## Dependencies:
* Python (2/3)
* request
* json
* slackclient

## Running
The JAMS Slack Bot is most easily run as an executable. From a terminal ensure you set permissions, and execute as follows:
```
chmod +x jams_bot.py
nohup python jams_bot.py &
```

## Available Commands:
* Run Job [Job Name] - Will Submit a Job within JAMS
* Find Job [Job Name] - Will locate all instances of a Job within JAMS
* Get Failed Jobs - List all Failed Jobs actively in the Monitor
* Help - List help information
