from configparser import ConfigParser
import praw
import re

BALANCE_CMD = r"balance"
WITHDRAW_CMD = r"withdraw (\d+)"

def main():
    # Get user agent, client id, secret, username, and password from ini file
    config_obj = ConfigParser()
    config_obj.read("config.ini")
    
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

    # Compile regular expressions
    bal_re = re.compile(BALANCE_CMD)
    wth_re = re.compile(WITHDRAW_CMD)
    
    # Continuously cycle through messages
    for message in reddit.inbox.stream(skip_existing=True):
        if isinstance(message, praw.reddit.models.Message):
            command(message, bal_re, wth_re)

def command(message, bal_re, wth_re):
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
        withdraw(message, wth_match.group(1))

def balance(message):
    message.mark_read()
    message.reply("BALANCE HERE")
    return

def withdraw(message, amount):
    message.mark_read()
    message.reply(f'{amount} SATS WITHDRAWN')
    return

if __name__ == "__main__":
    main()