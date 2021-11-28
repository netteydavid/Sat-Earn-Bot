from configparser import ConfigParser
import praw
import re

PAY_CMD = r"!pay (\d+)"

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

    # Compile regular expression
    pay_re = re.compile(PAY_CMD)
    
    # Continuously cycle through comments
    subreddits = reddit.subreddit(redditinfo["subreddits"])
    for comment in subreddits.stream.comments(skip_existing=True):
        command(comment, pay_re)

def command(comment, pay_re):
    # Get comment text
    text = comment.body.lower()
    
    # Find the first match
    pay_match = pay_re.search(text)

    # Check if there is a match
    if pay_match is not None:
        amount = pay_match.group(1)
        destination = comment.submission.author.name
        comment.reply(f'INVOICE FOR {amount} to {destination}')

if __name__ == "__main__":
    main()