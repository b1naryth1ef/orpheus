from tasks import task

from util.slack import SlackMessage

@task
def slack_async_message(job):
    return SlackMessage.send_raw(job['args'], job['kwargs'])

