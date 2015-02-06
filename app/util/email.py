import mandrill, logging

from emporium import app

log = logging.getLogger(__name__)
mandrill_client = mandrill.Mandrill(app.config.get("MANDRILL_API_KEY"))

class Email(object):
    def __init__(self):
        self.from_addr = "noreply@csgoemporium.com"
        self.from_name = "CSGO Emporium"
        self.to_addrs = []
        self.subject = ""
        self.body = ""

    def send(self):
        payload = {
            "from_email": self.from_addr,
            "from_name": self.from_name,
            "html": self.body,
            "subject": self.subject,
            "to": map(lambda i: {
                "email": i, "type": "to"
            }, self.to_addrs),
        }

        if app.config.get("ENV") != "PROD":
            log.debug("Would send email %s" % payload)
            return

        log.info("Sending email to %s" % self.to_addrs)
        mandrill_client.messages.send(message=payload)

