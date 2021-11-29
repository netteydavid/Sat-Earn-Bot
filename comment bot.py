from configparser import ConfigParser
import praw
import re
import lnpay_py
from lnpay_py.wallet import LNPayWallet
import math

PAY_CMD = r"!pay (\d+)"
FEE_MULTIPLIER = 1.005

def main():
    # Get user agent, client id, secret, username, and password from ini file
    config_obj = ConfigParser()
    config_obj.read("config.ini")
    
    userinfo = config_obj["USERINFO"]
    apiinfo = config_obj["APIINFO"]
    redditinfo = config_obj["REDDITINFO"]
    lnpayinfo = config_obj["LNPAYINFO"]

    # Get Reddit
    reddit = praw.Reddit(
        user_agent=apiinfo["user_agent"], 
        client_id=apiinfo["client_id"], 
        client_secret=apiinfo["client_secret"],
        username=userinfo["username"],
        password=userinfo["password"]
    )

    # Compile regular expression
    pay_re = re.compile(PAY_CMD)

    # Initilize LNPay
    lnpay_py.initialize(lnpayinfo["public_key"])
    
    # Continuously cycle through comments
    subreddits = reddit.subreddit(redditinfo["subreddits"])
    for comment in subreddits.stream.comments(skip_existing=True):
        command(comment, pay_re, lnpayinfo["wallet_invoice"])

def command(comment, pay_re, invoice_key):
    # Get comment text
    text = comment.body.lower()
    
    # Find the first match
    pay_match = pay_re.search(text)

    # Check if there is a match
    if pay_match is not None:
        # Get amount
        amount = int(pay_match.group(1))
        # Add fee
        amount = math.ceil(amount * FEE_MULTIPLIER)

        # Get payer and payee
        payer = comment.author.name
        payee = comment.submission.author.name

        # Get the wallet
        se_wallet = LNPayWallet(invoice_key)

        # Get invoice
        invoice_params = { 'num_satoshis': amount, 'memo': f'{payer} to {payee}', 'expiry': 1200 }
        invoice = se_wallet.create_invoice(invoice_params)

        # Reply
        # TODO: Host my own QR code generator
        comment.reply(f'Lightning Invoice: >!{invoice["payment_request"]}!< \n\n[Pay Invoice via QR Code](https://api.qrserver.com/v1/create-qr-code/?data={invoice["payment_request"]})')

if __name__ == "__main__":
    main()