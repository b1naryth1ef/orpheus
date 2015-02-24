from util.slack import SlackMessage

def slack_async_message(job):
    return SlackMessage.send_raw(job['args'], job['kwargs'])

