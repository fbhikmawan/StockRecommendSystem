import sys
sys.path.append('../Utility/python-twitter')

import os, time, datetime, pickle, re, configparser, pytz
import pandas as pd
from collections import Counter
from nltk.sentiment.vader import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import concurrent.futures
from tqdm import tqdm
import twitter

from Fetch_Data_Stock_US_Daily import getStocksList
  
def getSentiments(df):
    sid = SentimentIntensityAnalyzer()

    tweet_str = ""
    for tweet in df['Text']:
        tweet_str = tweet_str + " " + tweet

    print(sid.polarity_scores(tweet_str))
    # positiveWords = ["good", "buy", "great", "bull", "up", "beast", ]
    # negativeWords = ["bad", "sell", "terrible", "bear", "down"]
    # positive = 0
    # negative = 0

    # i=1
    # for tweet in totalTweets:
    #     for word in positiveWords:
    #         if word in tweet.text.encode('utf-8'):
    #             positive += 1
    #             print(i, tweet.text.encode('utf-8'))
    #             print(tweet.created_at)
    #     for word in negativeWords:
    #         if word in tweet.text.encode('utf-8'):
    #             negative += 1
    #             print(i, tweet.text.encode('utf-8'))
    #             print(tweet.created_at)
    #     i+=1

    # print("POSITIVE TWEETS: " + str(positive))
    # print("NEGATIVE TWEETS: " + str(negative))
    
def getWordCount(df, symbol, stocklist):
    ignore = ['the', 'rt', 'of', 'in', 'to', 'is', 'at', 'for', 'you', 'on', 'thursday', 'this', 'with', 'today', 'no', 'still', 
              'into', 'and', 'datacenter', 'https', 'all', 'play', 'stocks', 'watch', 'earnings', 'but', 'price', 'tomorrow', 
              'want', 'rating', 'open', 'shop', 'autonomous', 'be', 'money', 'reason', 'companies', 'company', 'that', 'when', 
              'made', 'new', 'who', 'president', 'was', 'market', 'looking', 'can', 'fbi', 'your', 'it', 'day', 'him', 'chief',  
              'united', 'historically', 'fires', 'investigating', 'from', 'while', 'profits', 'again', 'didn', 'upon', 'make', 
              'states', 'been', 'stock', 'let', 'put', 'basket', 'since', 'time', 'were', 'bought', 'q1', 'as', 'than', 'trading',
              'co', 'inc', 'keep', 'bank', 'target', 'has', 'news', 'by', 'asset', 'management', 'position', 'ipo', 'first', 
              'reaffirmed', 'there', 'expectations', 'after', 'bid', 'report', 'its', 'results', 'sellers', 'puts', 'out', 'may',
              'they', 'over', 'months', 'parent', 'magnitude', 'pack', 'quarter', 'what', 'plc', 'weight', 'given', 'looked', 'see',
              'weekly', 'review']
    words = []
    for tweet in df['Text']:
        words.extend(re.split(r'[-;:,./$#\'"’\s]\s*', tweet))
        
    counts = Counter(word for word in words if len(word) > 1 and word not in ignore and word.isdigit() == False)
    counts = counts.most_common()
    top5 = []
    
    for count in counts:
        match_stock_name = ''
        match_rate = 0.6
        str_count = str(count[0])
        len_count = len(str_count)
        for stock in stocklist:
            if stock == symbol: continue
            if stock.lower() in str_count:
                temp_match_rate = len(stock) / len_count 
                if temp_match_rate > match_rate:
                    match_stock_name = stock
                    match_rate = temp_match_rate
        #print(match_stock_name, match_rate, count)
        if len(match_stock_name) > 0: top5.append(match_stock_name)
        if len(top5) == 5: break
    return top5

    #print(counts)

def getSingleStockTwitter(api, dir, symbol, from_date, till_date):
    col = ['Date', 'ID', 'Text']
    filename = dir + symbol + ".csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename, usecols=col)
    else:
        df = pd.DataFrame(columns=col)
    
    symbol = "$"+symbol
    now = datetime.datetime.now()
    today = str(now.year) + "-" + str(now.month) + "-" + str(now.day)
    yesterday = now - datetime.timedelta(days=1)
    yesterday = str(yesterday.year) + "-" + str(yesterday.month) + "-" + str(yesterday.day)

    totalTweets = api.GetSearch(symbol + " stock", count=200, result_type="recent", lang='en', since=from_date, until=till_date)
    # print(idList)
    # print("idlist", len(idList))

    # if len(idList) == 0 : return

    # yesterdaysTweetID = idList[0].id

    # lastTweetID = yesterdaysTweetID

    # firstTweets = api.GetSearch(symbol, count=100, lang='en', since_id=lastTweetID)
    # lastTweetID = firstTweets[-1].id

    # nextTweets = []
    # totalTweets = []
    # prevLastTweetID = -1

    # while(prevLastTweetID != lastTweetID):
    #     prevLastTweetID = lastTweetID
    #     nextTweets = api.GetSearch(symbol, count=100, lang='en', since_id=lastTweetID)
    #     #last id of the 100 previous 100 tweets
    #     if(len(nextTweets)>0):
    #         lastTweetID = nextTweets[-1].id
    #     #add all tweets to one list
    #     totalTweets += nextTweets
        
    #     #print(totalTweets)
    #     #give Twitter servers a break
    #     time.sleep(1)
    
    for tweet in totalTweets:
        date = datetime.datetime.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=pytz.UTC)
        try:
            df.loc[len(df)] = [date.strftime("%Y-%m-%d %H:%M:%S"), tweet.id, tweet.text.lower()]
        except Exception as e:
            print("------------------")
            print("date", date)
            print("id", tweet.id)
            print("text", tweet.text)
            print("error", e)

    df = df.drop_duplicates(keep='last')
    df = df.sort_values(['Date'], ascending=[False]).reset_index(drop=True)
    df.to_csv(filename)
    return df


def updateSingleStockTwitterData(api, dir, symbol, from_date, till_date):
    startTime = time.time()
    df = getSingleStockTwitter(api, dir, symbol, from_date, till_date)
    return startTime, df


def updateStockTwitterData(symbols, from_date, till_date):
    Config = configparser.ConfigParser()
    Config.read("../../config.ini")
    dir = Config.get('Paths', 'TWITTER')

    if os.path.exists(dir) == False: 
        os.makedirs(dir)

    api_key = Config.get('Twitter', 'KEY')
    api_secret = Config.get('Twitter', 'SECRET')
    access_token_key = Config.get('Twitter', 'TOKEN_KEY')
    access_token_secret = Config.get('Twitter', 'TOKEN_SECRET')

    http = Config.get('Proxy', 'HTTP')
    https = Config.get('Proxy', 'HTTPS')

    proxies = {'http': http, 'https': https}

    stocklist = getStocksList()['Symbol'].values.tolist()
    
    api = twitter.Api(api_key, api_secret, access_token_key, access_token_secret, timeout = 15, proxies=proxies)
    
    for symbol in symbols:
        startTime, df = updateSingleStockTwitterData(api, dir, symbol, from_date, till_date)
        top5 = getWordCount(df, symbol, stocklist)
        print("hot correlation:", top5)
        getSentiments(df)

    # with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    #     # Start the load operations and mark each future with its URL
    #     future_to_stock = {executor.submit(updateSingleStockTwitterData, api, dir, symbol, from_date, till_date): symbol for symbol in symbols}
    #     for future in concurrent.futures.as_completed(future_to_stock):
    #         stock = future_to_stock[future]
    #         try:
    #             startTime, message = future.result()
    #         except Exception as exc:
    #             print('%r generated an exception: %s' % (stock, exc))
    #         else:
    #             outMessage = '%-*s fetched in:  %.4s seconds' % (6, stock, (time.time() - startTime))
    #             outMessage = outMessage + message
    #             print(outMessage)


if __name__ == "__main__":
    #nltk.download()
    #pd.set_option('precision', 3)
    #pd.set_option('display.width',1000)
    #warnings.filterwarnings('ignore', category=pd.io.pytables.PerformanceWarning)
    
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    updateStockTwitterData(["NVDA"], "1990-01-01", now)


    # date = datetime.datetime.strptime('Thu Apr 23 13:38:19 +0000 2009', '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=pytz.UTC)
    # print("Date", date)
    # df.loc[len(df)] = [date]
    # print(df)
    # stockName = input("Please enter the ticker name for the desired stock (Example: For Nvidia type NVDA): ") 
    # totalTweets = getStockTweets(stockName)
    # # for tweet in totalTweets:
    # #     print(tweet)
    # #     break
    # # return
    # if len(totalTweets) == 0: return
    # getWordCount(totalTweets)
    # 