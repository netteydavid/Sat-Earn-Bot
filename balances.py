import sqlite3
import lnpay_py
from lnpay_py.lntx import LNPayLnTx
import praw
import schedule
import time
from configparser import ConfigParser

def main():

    # Get user agent, client id, secret, username, and password from ini file
    config_obj = ConfigParser()
    config_obj.read("config.ini")

    lnpayinfo = config_obj["LNPAYINFO"]
    userinfo = config_obj["USERINFO"]
    apiinfo = config_obj["APIINFO"]
    redditinfo = config_obj["REDDITINFO"]

    # Get Reddit
    reddit = praw.Reddit(
        user_agent=apiinfo["user_agent"], 
        client_id=apiinfo["client_id"], 
        client_secret=apiinfo["client_secret"],
        username=userinfo["username"],
        password=userinfo["password"]
    )

    lnpay_py.initialize(lnpayinfo["public_key"])

    schedule.every(1).minutes.do(checkInvoices, reddit=reddit)
    while True:
        schedule.run_pending()
        time.sleep(1)
    return

def getAllInvoices():
    con = sqlite3.connect('satearn.db')
    cur = con.cursor()
    cur.execute(f'SELECT * FROM Invoices')
    rows = cur.fetchall()
    con.close()
    return rows

def updateBalance(redditor, amount):
    con = sqlite3.connect('satearn.db')
    cur = con.cursor()
    cur.execute(f'SELECT Balance FROM Balances WHERE User = \'{redditor}\'')
    old_balance = cur.fetchone()
    if old_balance == None:
        cur.execute(f'INSERT INTO Balances VALUES (\'{redditor}\', {amount})')
    else:
        cur.execute(f'UPDATE Balances SET Balance = {old_balance[0] + amount} WHERE User = \'{redditor}\'')
    con.commit()
    con.close()
    return

def removeInvoice(invoice):
    con = sqlite3.connect('satearn.db')
    cur = con.cursor()
    cur.execute(f'DELETE FROM Invoices WHERE Invoice = \'{invoice}\'')
    con.commit()
    con.close()

def checkInvoices(reddit):
    # Retrieve all pending invoices
    invoices = getAllInvoices()
    # Check the status of each invoice
    for invoice in invoices:
        tx = LNPayLnTx(invoice[0])
        info = tx.get_info()
        comment: praw.reddit.models.Comment = reddit.comment(invoice[1])
        if info["settled"] == 1:
            print(f'Invoice {info["id"]} settled!')
            payee = comment.parent().author.name
            # Update balance
            updateBalance(payee, invoice[2])
            print("Balance updated")
            # Remove the invoice
            removeInvoice(invoice[0])
            print("Invoice removed")

            # Get the first reply
            comment.refresh()
            reply = [r for r in comment.replies if r.author.name == "satearn_bot"]

            if len(reply) > 0:
                # Edit the comment
                reply[0].edit(f'/u/{comment.author.name} has paid /u/{payee} {invoice[2]} sats!')
                print("Comment edited")

        elif info["expires_at"] <= int(time.time()):
            print(f'Invoice {info["id"]} expired!')
            # Remove the invoice
            removeInvoice(invoice[0])
            print("Invoice removed")

            # Get the first reply
            comment.refresh()
            reply = [r for r in comment.replies if r.author.name == "satearn_bot"]
            
            if len(reply) > 0:
                # Edit the comment
                reply[0].edit(f'Invoice Expired.')
                print("Comment edited")
    return



if __name__ == "__main__":
    main()