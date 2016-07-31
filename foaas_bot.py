import logging
import requests
import json
import time
import random
import re
from threading import Timer
from slackclient import SlackClient


logging.basicConfig(level=logging.WARN,
                    format='%(asctime)s %(name)-12s %(levelname)-6s - %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('foaas_bot')
logger.setLevel(logging.INFO)


class FoaasBot(object):
    # List of regex patterns that will trigger a response every time.
    patterns = []  # [re.compile("(test)", re.I)]

    # every 12 hours
    FOAAS_UPDATE_INTERVAL = 60**2 * 12

    def __init__(self, token, name, company=None, response_prob=10):
        self.bot_access_token = token
        self.bot_name = name
        self.company = company
        self.response_prob = response_prob  # out of 100
        self.headers = {'Accept': 'application/json'}
        self.stay_alive = True
        self.foaas = []
        self.client = None

    def get_operations(self):
        try:
            req = requests.get('http://www.foaas.com/operations', headers=self.headers)
            operations = json.loads(req.text)
            return [op for op in operations if op['name'] != 'Version']
        except Exception as e:
            logger.error(e)

        # If there was an error, just return the ops in its current state
        return self.foaas

    def post_message(self, text, channel):
        try:
            self.client.api_call("chat.postMessage",
                                 channel=channel,
                                 text=text,
                                 as_user="true",
                                 username=self.bot_name,
                                 link_names=1)
        except Exception as e:
            logger.error(e)

    def get_name(self, user):
        try:
            info = self.client.api_call("users.info", user=user)
            logger.debug(info)
            if info['ok']:
                return info['user']['profile']['first_name']
        except Exception as e:
            logger.error(e)
        return None

    def is_private_channel(self, channel):
        try:
            info = self.client.api_call("channels.info", channel=channel)
            logger.debug(info)
            if not info['ok'] and info['error'] == 'channel_not_found':
                return True
        except Exception as e:
            logger.error(e)
        return False

    def connect(self):
        self.client = SlackClient(bot_access_token)
        return self.client.rtm_connect()

    def should_respond(self, event, user):
        message = event["text"]
        if self.is_private_channel(event['channel']):
            logger.info("message on private channel")
            respond = True
        elif any([p.search(message) is not None for p in self.patterns]):
            logger.debug("pattern matched!")
            respond = True
        else:
            respond = random.randint(1, 100) <= self.response_prob

        respond &= user != 'slackbot'
        return respond

    def get_foaas_message(self, user):
        if len(self.foaas) > 0:
            valid_url = False
            url = None
            while not valid_url:
                # Pick a new message url
                action = random.choice(self.foaas)
                fields = [f['field'] for f in action['fields']]
                url = action['url']
                if ('name' in fields and user is None) or ('company' in fields and self.company is None):
                    continue
                # Replace fields in the url
                if 'from' in fields:
                    url = url.replace(':from', self.bot_name)
                if 'name' in fields:
                    url = url.replace(':name', user)
                if 'company' in fields:
                    url = url.replace(':company', self.company)

                # Check that it is valid
                url = 'http://www.foaas.com' + url
                valid_url = '/:' not in url
                if not valid_url:
                    logger.info("bad url: {}".format(url))

            # Get the message from FOAAS
            try:
                logger.info("foaas url: {}".format(url))
                req = requests.get(url, headers=self.headers)
                foaas_message = json.loads(req.text)
                return foaas_message['message']

            except:
                logger.error("Failed to get FOAAS message.")

        return None

    def process_events(self, events):
        for event in events:
            logger.debug(event)
            if "type" in event:
                if event["type"] == "hello":
                    logger.info("Connected to Slack.")

                elif event["type"] == "message" and "text" and "user" in event and "bot_id" not in event:
                    # Get the name of the user who sent the message
                    user = self.get_name(event["user"])
                    respond = self.should_respond(event, user)
                    logger.info("user: {}  respond: {}".format(user, respond))
                    if respond:
                        # Get a new foaas message
                        message = self.get_foaas_message(user)
                        if message is not None:
                            logger.info("posting: {}".format(message.encode('utf-8')))
                            # Send it
                            self.post_message(message, channel=event["channel"])

    def get_events(self):
        for i in xrange(3):
            try:
                events = self.client.rtm_read()
                if len(events) > 0:
                    logger.debug(events)
                return events

            except:
                logger.warn("Connection closed. Trying to reconnect.")
                if not self.connect():
                    logger.warn("Reconnect failed.")
        return None

    def is_alive(self):
        try:
            info = self.client.api_call("api.test")
            return info['ok']
        except:
            return False

    def update_ops_loop(self):
        self.foaas = self.get_operations()
        logger.info("foaas messages updated.")
        Timer(self.FOAAS_UPDATE_INTERVAL, self.update_ops_loop, ()).start()

    def run(self):
        self.update_ops_loop()

        if self.connect():
            while self.stay_alive:
                events = self.get_events()
                if events is None:
                    break

                self.process_events(events)
                time.sleep(1)

        else:
            logger.error("Connection to Slack failed.")

    def stop(self):
        self.stay_alive = False

if __name__ == '__main__':
    import signal
    import os

    assert "SLACK_TOKEN" in os.environ
    assert "BOT_NAME" in os.environ

    bot_access_token = os.environ['SLACK_TOKEN']
    bot_name = os.environ['BOT_NAME']
    company_name = os.environ['COMPANY_NAME'] if "COMPANY_NAME" in os.environ else None
    response_p = int(os.environ['RESPONSE_PROB']) if "RESPONSE_PROB" in os.environ else 10

    foaas_bot = FoaasBot(bot_access_token, bot_name, company=company_name, response_prob=response_p)

    def signal_handler(signum, frame):
        print 'Signal handler called with signal', signum
        foaas_bot.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    foaas_bot.run()
