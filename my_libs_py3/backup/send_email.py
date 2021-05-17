import smtplib, ssl
from email.parser import Parser
import getpass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from my_lib import *

def send_email(body_html, sent_from="lgyhz1234@gmail.com", sent_to="lgyhz1234@gmail.com", title="Daily Position", body_content=""):
    
        
    must_have = readgateway(2)
    
    sent_to = sent_to.strip('[]').split(',')

    

    

    if len(sent_to) > 1:
    
        headers = Parser().parsestr('From: <' + sent_from + '>\n'
                'To: <' + ", ".join(sent_to) + '>\n'
                'Subject: ' + title  + '\n'
                '\n' +
                body_content +
                '\n')
    else:
         headers = Parser().parsestr('From: <' + sent_from + '>\n'
                'To: <' + sent_to[0] + '>\n'
                'Subject: ' + title  + '\n'
                '\n' +
                body_content +
                '\n')

    message = MIMEMultipart("alternative")
    message["Subject"] = title
    message["From"] = sent_from
    
    
    plain = MIMEText(body_content,"plain")
    message.attach(plain)
    if body_html is not None:
        message.attach(MIMEText(body_html,"html"))

    

    #  Now the header items can be accessed as a dictionary:
    print ('To: %s' % headers['to'])
    print ('From: %s' % headers['from'])
    print ('Subject: %s' % headers['subject'])

    context = ssl.create_default_context()    
    s= smtplib.SMTP("smtp.gmail.com")
       
        #s.connect("stmp.gmail.com")
    
    s.ehlo()
    s.starttls()
    s.login(sent_from, must_have)

    for receiver in sent_to:
        message["To"] = receiver
        s.sendmail(sent_from,receiver,message.as_string())    
    s.close()
if __name__ == "__main__":
    send_email()