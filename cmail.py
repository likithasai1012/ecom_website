import smtplib
from email.message import EmailMessage
def send_mail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465) #obj creation for gmail server
    server.login('sunkarababyjahnavi@gmail.com','rtlu nxke ikek xnkj') #login to gmail
    msg=EmailMessage() #email format obj creation
    msg['FROM']='sunkarababyjahnavi@gmail.com'
    msg['TO']=to
    msg['SUBJECT']=subject
    msg.set_content(body)
    server.send_message(msg) #mail sending 
    server.close() #closing the server obj