#!/usr/bin/python
# -*- coding: UTF-8 -*-

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
 
# python 2.3.*: email.Utils email.Encoders
from email.utils import COMMASPACE,formatdate
from email import encoders
 
import os
 
#server['name'], server['user'], server['passwd']
#

def send_mail(server, fro, to, subject, text, files=[]): 
    #assert type(server) == dict 
    assert type(to) == list 
    assert type(files) == list 
 
    msg = MIMEMultipart() 
    msg['From'] = fro 
    msg['Subject'] = subject 
    msg['To'] = COMMASPACE.join(to) #COMMASPACE==', ' 
    msg['Date'] = formatdate(localtime=True) 
    msg.attach(MIMEText(text)) 
 
    for file in files: 
        part = MIMEBase('application', 'octet-stream') #'octet-stream': binary data 
        part.set_payload(open(file, 'rb'.read())) 
        encoders.encode_base64(part) 
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file)) 
        msg.attach(part) 
 
    import smtplib 
    smtp = smtplib.SMTP(server) 
    #smtp.login(server['user'], server['passwd']) 
    smtp.set_debuglevel(1)
    smtp.sendmail(fro, to, msg.as_string()) 
    smtp.close()
    
if __name__ == '__main__':
    server = "135.5.2.65"
    #server = "135.251.50.68"
    #server = "127.0.0.1:7777"
    #server = "135.253.8.94"   #"mailhost.alcatel-lucent.com"
    fro = "felix.ma@alcatel-lucent.com"
    to  = ["felix.ma@alcatel-lucent.com"]
    subject = "subject"
    text = "text"

    send_mail(server, fro, to, subject, text)

