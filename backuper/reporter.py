
import sys

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders

import logging


class Reporter :

    admins = []
    settings = {}

    def init(self, settings) :
        self.admins = settings['admins']
        self.settings = settings['email']
        return

    def report(self, subject, message) :
        try :
            server = smtplib.SMTP_SSL('%s:%i' % (self.settings['SMTP'], self.settings['PORT']))
            server.login(self.settings['LOGIN'], self.settings['PASS'])
            
            msg = MIMEMultipart()
            msg['From'] = self.settings['EMAIL']
            msg['To'] = ", ".join(self.admins)
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'html'))

            server.sendmail(self.settings['EMAIL'], self.admins, msg.as_string())
            server.quit()

        except :
            logging.error("ERROR sending email: %s" % (sys.exc_info()[0],))
