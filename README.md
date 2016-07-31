# foaas_slackbot
A slackbot utilizing http://www.foaas.com/

Create a custom bot for your Slack team and invite it to any channels you want it to take part in. It will randomly respond to comments with messages from FOAAS. Sending a private message to the bot will always receive a response. Custom keywords or regex patterns can be defined in the python file that will always trigger a response as well.

### Usage
The docker-compose file can be used for running the image, but the environment variables defined within will need to be modified for each specific use case. They can also be defined in a standard 'docker run' command if that is preferred. 

The variables are as follows:
* SLACK_TOKEN - Obtained by creating a slack bot for your Slack team.
* BOT_NAME - The name of the slack bot created for Slack team.
* COMPANY_NAME (optional) - Used for FOAAS messages that require a company name.
* RESPONSE_PROB (optional) - Probability of responding to any message (out of 100). Defaults to 20.
