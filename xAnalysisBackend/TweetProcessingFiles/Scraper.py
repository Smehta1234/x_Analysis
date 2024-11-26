from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from redis import Redis  # Import Redis client
from TweetProcessor.utils.redis_client import get_redis_connection

load_dotenv()

def initialize_browser():
    options = Options()
    # options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Disable JavaScript
    options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.javascript": 2
    })

    # Disable CSS (by blocking stylesheets)
    options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.stylesheets": 2
    })

    browser = webdriver.Chrome(options=options)
    actions = ActionChains(browser)
    return browser, actions

def login_to_twitter(browser, wait, username_str, password_str, verification_str=None):
    try:
        browser.get("https://x.com/i/flow/login")
        print("trying to log in")
        username = wait.until(EC.presence_of_element_located((By.NAME, 'text')))
        username.send_keys(username_str)
        print("logged in")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
        print("next clicked")
        if verification_str:
            try:
                verification_input = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[data-text-id='ocfEnterTextTextInput']")))
                verification_input.send_keys(verification_str)
                wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
            except:
                print("Verification input skipped")

        password = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        password.send_keys(password_str)
        print("password sent")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))).click()

        # Confirm login success
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="SearchBox_Search_Input"]')))
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False


def search_twitter(browser, wait, search_term, start_date, end_date):
    try:
        search_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="SearchBox_Search_Input"]')))
        search_box.click()
        search_box.send_keys(Keys.CONTROL + 'a')
        search_box.send_keys(Keys.DELETE)
        search_query = f"{search_term} since:{start_date} until:{end_date}"
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)  # Short sleep for results to load
    except Exception as e:
        print(f"Search failed: {e}")


def collect_tweets(browser, wait, redis_conn, stream_name="tweets_stream"):
    tweets = []
    try:
        match = False
        while not match:
            # Collect tweets from the current view
            tweet_elements = browser.find_elements(By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')
            for tweet_element in tweet_elements:
                # Extract tweet text
                try:
                    tweet_text_parts = tweet_element.find_elements(By.XPATH, ".//div[@data-testid='tweetText']//span")
                    tweet_text = " ".join([part.text for part in tweet_text_parts])
                except:
                    tweet_text = ""

                # Extract tweet date and time
                try:
                    tweet_time_element = tweet_element.find_element(By.XPATH, ".//time")
                    tweet_datetime = tweet_time_element.get_attribute("datetime")  # ISO 8601 format
                    tweet_date = tweet_datetime.split("T")[0]
                    tweet_time = tweet_datetime.split("T")[1].split(".")[0]
                except:
                    tweet_date, tweet_time = "", ""

                # Extract tweet engagement metrics from aria-label
                try:
                    engagement_element = tweet_element.find_element(By.XPATH, ".//div[@role='group']")
                    engagement_text = engagement_element.get_attribute("aria-label")

                    # Parse engagement metrics
                    replies = reposts = likes = bookmarks = views = "0"
                    if engagement_text:
                        engagement_parts = engagement_text.split(", ")
                        for part in engagement_parts:
                            if "replies" in part:
                                replies = part.split()[0]
                            elif "reposts" in part:
                                reposts = part.split()[0]
                            elif "likes" in part:
                                likes = part.split()[0]
                            elif "bookmarks" in part:
                                bookmarks = part.split()[0]
                            elif "views" in part:
                                views = part.split()[0]
                except:
                    replies = reposts = likes = bookmarks = views = "0"

                # Add collected tweet data to list if text is not empty
                if tweet_text.strip() != "":
                    tweet_data = {
                        "text": tweet_text,
                        "date": tweet_date,
                        "time": tweet_time,
                        "replies": replies,
                        "reposts": reposts,
                        "likes": likes,
                        "bookmarks": bookmarks,
                        "views": views
                    }
                    tweets.append(tweet_data)
                    print(tweet_data)  # Print tweet details for reference

                    # Add tweet to the Redis stream
                    redis_conn.xadd(stream_name, tweet_data)

            # Scroll to load more tweets
            last_count = browser.execute_script("return document.body.scrollHeight")
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Allow time for new tweets to load
            len_of_page = browser.execute_script("return document.body.scrollHeight")

            # Check if scrolling resulted in new content
            if last_count == len_of_page:
                match = True

        print("Scrolling completed.")
    except Exception as e:
        print(f"Error occurred while scrolling or collecting tweets. Details: {e}")
        browser.quit()

    return tweets


def scrape_twitter(search_term):
    # Load Twitter credentials from environment variables
    username = os.getenv("TWITTER_USERNAME")
    password = os.getenv("TWITTER_PASSWORD")
    verification = os.getenv("TWITTER_VERIFICATION")

    # Initialize Redis connection
    redis_conn = get_redis_connection()

    # Initialize the browser and WebDriverWait
    browser, actions = initialize_browser()
    wait = WebDriverWait(browser, 15)

    try:
        # Log in to Twitter
        if login_to_twitter(browser, wait, username, password, verification):
            # Start collecting tweets in 5-day intervals
            start_date = datetime.now() - timedelta(days=25)  # Adjust as needed
            current_date = datetime.now()
            all_tweets = []  # To store all collected tweets

            while start_date < current_date:
                # Calculate the end date for the 5-day interval
                end_date = start_date + timedelta(days=5)
                if end_date > current_date:
                    end_date = current_date  # Limit the end date to the current date

                print(f"Collecting tweets from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

                # Search Twitter for tweets within the 5-day interval
                search_twitter(browser, wait, search_term, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

                # Collect tweets and add to the Redis stream
                tweets = collect_tweets(browser, wait, redis_conn)
                all_tweets.extend(tweets)

                # Move to the next 5-day interval
                start_date = end_date

            # Optionally save all tweets to a file or return them


    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        browser.quit()

    # return tweets


def main():
    # Define search parameters
    search_term = "zomato"

    # Define date range (for example, past week)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=25)).strftime("%Y-%m-%d")

    # Call the scrape_twitter function
    tweets = scrape_twitter(search_term, start_date, end_date)

    # Print the results


if __name__ == "__main__":
    main()


