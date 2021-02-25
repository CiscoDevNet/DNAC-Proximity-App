from webexteamssdk import WebexTeamsAPI, ApiError
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# '''This Lambda function handles BOT's conversation and actions'''

### BOT INFO - TO COME FROM VAULT or Hardcode below ###
# BOT_TOKEN = ''
# BOT_ACCOUNT = ''
# BOT_ID = ''

intro = """ ### Welcome Pandemic Prevention Team! 
**Pandemia** will help you lookup a pandemic positive employee!
I do support a few text commands:
- **Help** - will present this message again.
- **Search** - will bring up the contact tracing form.
- any other text will just be disregarded for now. 

⚠️ Mention me in a space using **@Proximity** to get my attention. This does not apply in a 1:1 room
"""

fallback_msg = """ ## Je suis un Bot. I chat, therefore I am.
try *Help* to get started
"""

with open('card.json') as c:
    cards = json.load(c)

api = WebexTeamsAPI(access_token=BOT_TOKEN)

# ```Default Handler function, receives webhook events posted to AWS API Gateway```
def handle(event, context):
    logger.info('### EVENT INFO \n {}'.format(json.dumps(event)))
    if 'detail-type' in event:
        logger.info('### KEEP ALIVE FUNCTION')
    elif event['resource'] == 'memberships':
        bot_membership_handler(event)
    else:
        if event['data']['personEmail'] != 'pandemia@webex.bot':
            bot_msg_handler(event)

## Function parses payload and posts form to capture user submission
def bot_msg_handler(event):
    logger.info('### MESSAGE HANDLER FUNCTION')
    incoming_msg = api.messages.get(messageId=event['data']['id'])
    text = incoming_msg.text.lower()
    text = str(text)
    text = text.replace("proximity ", "")
    if text == 'help':
        try:
            msg = api.messages.create(roomId=incoming_msg.roomId, markdown=intro)
            msg = api.messages.create(roomId=incoming_msg.roomId, text='\n', attachments=cards)
        except ApiError as e:
            logger.info(e)
    elif text == 'search':
        try:
            msg = api.messages.create(roomId=incoming_msg.roomId, text='\n', attachments=cards)
        except ApiError as e:
            logger.info(e)
    else:
        try:
            msg = api.messages.create(roomId=incoming_msg.roomId, markdown=fallback_msg)
        except ApiError as e:
            logger.info(e)


def bot_membership_handler(event):
    logger.info('### MEMBERSHIP HANDLER FUNCTION')
    msg = api.messages.create(roomId=event['data']['roomId'], markdown=intro)
    msg = api.messages.create(roomId=event['data']['roomId'], text='\n', attachments=cards)

