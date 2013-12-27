from google.appengine.api import mail

__author__ = 'Omri'


class Email:

    def __init__(self):
        pass


    def send_mail(self, email, sender_address, subject, body):
        user_address = email

        if not mail.is_email_valid(user_address):
            pass
        else:
            mail.send_mail(sender_address, user_address, subject, body)

    def send_registration(self, email , user_id, course_name, course_hour, course_date):



            sender_address = "classter.app@gmail.com"
            subject = "Confirm your registration to course: " + course_name
            body = """This is a confirmation email for user ID: %s.
    `You are now registered to %s at %s on %s.""" % (user_id, course_name, course_hour, course_date)

            self.send_mail(self, email,sender_address , subject, body)

    def send_mail_to_group(self, email_arr, sender_address, subject, body):
        for i in range(len(email_arr)):
            user_address = email_arr[i]

            if not mail.is_email_valid(user_address):
                pass
            else:
                mail.send_mail(sender_address, user_address, subject, body)