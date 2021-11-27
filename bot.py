from configparser import ConfigParser
import praw

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
    
    # Continuously cycle through comments
    subreddits = reddit.subreddit(redditinfo["subreddits"])
    for comment in subreddits.stream.comments():
        print(comment.body)

if __name__ == "__main__":
    main()