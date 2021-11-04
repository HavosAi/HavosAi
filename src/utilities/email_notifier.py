import smtplib
from email.mime.text import MIMEText

class EmailNotifier:

	def __init__(self, login = "Ceres2030.notification@gmail.com", password = "123Qwaszx456", smtp_client = "smtp.gmail.com:587"):
		self.login = login
		self.password = password
		self.smtp_client = smtp_client

	def send_email_notification(self, text, subject, email):
		if email is None or email.strip() == "":
			return
		try:
		    msg = MIMEText(text)

		    msg['Subject'] = subject
		    msg['To'] = email
		    s = smtplib.SMTP(self.smtp_client)
		    s.starttls()
		    s.login(self.login, self.password)
		    s.sendmail(self.login, [email], msg.as_string())
		    s.quit() 
		except:
			print("Email notifiction wasnot sent. Check email, please")