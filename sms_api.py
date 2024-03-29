#! .env/bin/python

from twilio import TwilioRestException
from twilio.rest import TwilioRestClient
import config
import pyodbc

account_sid = config.TWILIO_ACCOUNT_SID # Your Account SID from www.twilio.com/console
auth_token = config.TWILIO_AUTH_TOKEN   # Your Auth Token from www.twilio.com/console
client = TwilioRestClient(account_sid, auth_token)


class ServerError(Exception):
    pass


class AzureSQLDatabase(object):
    connection = None
    cursor = None

    def __init__(self):
        self.connection = pyodbc.connect(config.CONN_STRING)
        self.cursor = self.connection.cursor()

    def query(self, query, params):
        return self.cursor.execute(query, params)

    def commit(self):
        return self.connection.commit()

    def __del__(self):
        self.connection.close()


def main():
    """
    Twilio REST API for SMS/MMS with Python Helper
    :param: twilio authentication
    :type: string
    :return: message sid
    """

    try:
        conn = AzureSQLDatabase()
        params = 1, 0
        sql = "select top 1 a.alertid, a.alertdatetime, a.alerttype, a.contactid, a.alerttext, " \
              "tc.contactname, tc.contactnumber " \
              "from alerts a inner join teamcontacts tc on a.contactid = tc.contactid " \
              "where a.alertqueued = ? and a.alertsent = ?; "
        cursor = conn.query(sql, params)
        columns = [column[0] for column in cursor.description]

        for row in cursor.fetchall():
            alert_id = row[0]
            alert_date = row[1].strftime('%Y-%m-%d %H:%M:%S')
            alert_type = row[2]
            contact_id = row[3]
            alert_text = row[4]
            contact_name = row[5]
            contact_number = "1" + str(row[6])

            try:
                message = client.messages.create(
                    body=alert_text,
                    to=contact_number,  # Replace with your phone number
                    from_=config.TWILIO_NUMBER)  # Replace with your Twilio number

                # save the twilio sid to the database
                params = (message.sid, alert_date, alert_id)
                conn.query("update alerts set sid = ?, alertqueued = 0, alertsent = 1, alertsentdate = ? "
                           "where alertid = ? ", params)

                conn.commit()
                print(message.sid)

                with open('/var/www/html/qwikcut-sms-api/log/sms_log.txt', 'a') as f:
                    f.write('{0} - QC+ Twilio API sent message to {1}:{2} on {3}\n'.format(message.sid,
                                                                                         contact_name,
                                                                                         contact_number,
                                                                                         alert_date))

            except TwilioRestException as e:
                # handle the exception in the database so we can move on
                params = alert_id
                conn.query("update alerts set sid = -1, alertqueued = 0, alertsent = 1"
                           "where alertid = ? ", params)

                conn.commit()
                print(e)

                with open('/var/www/html/qwikcut-sms-api/log/sms_log.txt', 'a') as f:
                    f.write('{0} ** QC+ Twilio API could not send shooter message to {1}:{2} on {3}\n'.format(
                        e,
                        contact_name,
                        contact_number,
                        alert_date)
                    )

    except ServerError as e:
        error = str(e)


if __name__ == '__main__':
    main()

