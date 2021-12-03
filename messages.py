from configparser import ConfigParser
import praw
import re
import sqlite3
from lnpay_py.wallet import LNPayWallet

BALANCE_CMD = r"balance"
WITHDRAW_CMD = r"withdraw (\d+)"

def main():
    # Get user agent, client id, secret, username, and password from ini file
    config_obj = ConfigParser()
    config_obj.read("config.ini")
    
    userinfo = config_obj["USERINFO"]
    apiinfo = config_obj["APIINFO"]
    lnpayinfo = config_obj["LNPAYINFO"]

    # Get Reddit
    reddit = praw.Reddit(
        user_agent=apiinfo["user_agent"], 
        client_id=apiinfo["client_id"], 
        client_secret=apiinfo["client_secret"],
        username=userinfo["username"],
        password=userinfo["password"]
    )

    # Compile regular expressions
    bal_re = re.compile(BALANCE_CMD)
    wth_re = re.compile(WITHDRAW_CMD)
    
    # Continuously cycle through messages
    for message in reddit.inbox.stream(skip_existing=True):
        if isinstance(message, praw.reddit.models.Message):
            command(message, bal_re, wth_re, lnpayinfo["wallet_withdraw"])

def command(message, bal_re, wth_re, withdraw_key):
    text = message.body.lower()
    
    # Find the matches
    bal_match = bal_re.search(text)
    wth_match = wth_re.search(text)

    # Get the positions
    bal_pos = -1
    wth_pos = -1
    
    if bal_match is not None:
        bal_pos = text.find(bal_match.group(0))
    if wth_match is not None:
        wth_pos = text.find(wth_match.group(0))

    # Execute the first command found
    if (bal_pos < wth_pos and bal_pos > -1) or (bal_pos > -1 and wth_pos < 0):
        balance(message)
    elif (wth_pos < bal_pos and wth_pos > -1) or (wth_pos > -1 and bal_pos < 0):
        withdraw(message, wth_match.group(1), withdraw_key)

def balance(message: praw.reddit.models.Message):
    message.mark_read()
    sender = message.author.name
    print("Balance request recieved from " + sender)
    amt = getBalance(sender)
    sat = "sat" if amt == 1 else "sats"
    withdraw_msg = "\nTo withdraw, send \"!withdraw\" followed by a space and the amount you want to withdraw. \nExample: !withdraw 100"
    message.reply(f'You have a balance of {amt} {sat}.{withdraw_msg if amt > 0 else ""}')
    print("Message sent")

def getBalance(redditor):
    con = sqlite3.connect('satearn.db')
    cur = con.cursor()
    cur.execute(f'SELECT Balance FROM Balances WHERE User = \'{redditor}\'')
    balance = cur.fetchone()
    if balance == None:
        return 0
    else:
        return balance[0]

def withdraw(message, amount, key):
    message.mark_read()

    if amount == 0:
        message.reply("Please withdraw a nonzero amount")
        return

    redditor = message.author.name

    balance = getBalance(redditor)

    if balance == 0:
        message.reply("You have no balance! Get some sats at /r/satearn")
        return

    if amount > balance:
        message.reply(f'Please withdraw an amount less than or equal your balance. Balance: {balance} sats')
        return

    wallet = LNPayWallet(key)
    params = {
        'num_satoshis': amount,
        'memo': f'{redditor} withdrawal'
    }

    lnurl = wallet.get_lnurl(params)

    message.reply(f'LN-Url: >!{lnurl}!< \n\n[Withdraw via QR Code](https://api.qrserver.com/v1/create-qr-code/?data={lnurl})')

    #TODO: Save lnurl and redditor name. Find a way to check the status of an lnurl.
    return

if __name__ == "__main__":
    main()