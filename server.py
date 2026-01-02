'''
The goal of this app is to periodically fetch unread emails from sce.sjsu@gmail.com.
The emails will be parsed to see if they are Venmo receipts and contain the description "SCE Membership"
If they are, then we can create the MongoDB document and insert into Clark's database, then we mark the email as read

Gmail API Reference: https://developers.google.com/workspace/gmail/api/guides
For Python: https://developers.google.com/gmail/api/quickstart/python

One of the biggest hurdles is authentication: https://developers.google.com/identity/protocols/oauth2
'''