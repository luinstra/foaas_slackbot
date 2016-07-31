# foaas_slackbot
A slackbot utilizing http://www.foaas.com/

### Usage
The docker-compose file can be used for running the image, but the environment variables defined within will need to be modified for each specific use case. They can also be defined in a standard 'docker run' command if that is preferred. 

The variables are as follows:
* SLACK_TOKEN - Obtained by creating a slack bot for your channel.
* BOT_NAME - The name of the slack bot created for your channel.
* COMPANY_NAME (optional) - Used for FOAAS messages that require a company name.
* RESPONSE_PROB (optional) - Probability of responding to any message (out of 100). Defaults to 20.
