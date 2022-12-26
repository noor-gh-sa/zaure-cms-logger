import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def main(msg: func.ServiceBusMessage):
    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info(f"Python ServiceBus queue trigger processed message with ID: { notification_id } on: { datetime.utcnow() }")
 
    connection = psycopg2.connect(user = "pgadmin@project3db-01",
                                  password = "Admin@123",
                                  host = "project3db-01.postgres.database.azure.com",
                                  port = "5432",
                                  database = "techconfdb")
    cursor = connection.cursor()

    try:
        notification_query = '''SELECT subject, message 
                                FROM Notification
                                WHERE id = %s;'''

        cursor.execute(notification_query, (notification_id,))
        notification = cursor.fetchone()

        subject = notification[0]
        message = notification[1]
        
        attendees_query = 'SELECT first_name, email FROM Attendee;'
        cursor.execute(attendees_query)
        attendees = cursor.fetchall() 
   
        for attendee in attendees:
            first_name = attendee[0]
            email = attendee[1]
            custom_subject = f'Hello, { first_name }: { subject }'
            send_email(email, custom_subject, message)

        completed_date = datetime.utcnow()
        status = f'{ len(attendees) } Tech Conf 2022 attendees notified.'

        update_query = '''UPDATE Notification 
                                SET completed_date = %s, status = %s 
                                WHERE id = %s;'''
        cursor.execute(update_query, (completed_date, status, notification_id))
        connection.commit()
        count = cursor.rowcount
        logging.info(f"{ count } records successfully updated.")

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    
    # Ensure to close database connection.
    finally:
        if(connection):
            cursor.close()
            connection.close()
            print("Connection to PostgreSQL database successfully closed.")


# Send message function using Send Grid API.
def send_email(email, subject, body):
    message = Mail(
        from_email="noor.2023.alghamdi@outlook.com",
        to_emails=email,
        subject=subject,
        plain_text_content=body
    )
    try:
        sg = SendGridAPIClient("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")
        sg.send(message)
    except Exception as e:
        logging.info("Unable to send message using SendGrid API.")