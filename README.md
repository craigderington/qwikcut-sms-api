### QwikCut - Twilio SMS Gateway API

This repo contains the QC+ web app's micro-service Twilio API as the application's text messaging platform for
all users of the QwikCut.com system.

Usage:

* Cron runs sms_api.py every minute between 8 am and 8 pm.
* crontab -e 0 8-17 * * * /path/to/python/environment /path/to/file/sms_api.py
* sms_api queries database for queued message alerts
* query sets messaging params
* twilio sends message
* query updates the QC+ alert table with the message id
