# -*- coding: utf-8 -*-
"""
Sarah Wigodsky
DATA 602 Advanced Programming
Assignment 2 - Trading Cryptocurrencies
"""
import bs4          #import BeautifulSoup4 for process information from webpages
import json         #to process APIs   
import urllib.request      #to process urls
import datetime            #to determine the current date and time 
from dateutil import parser
import pandas as pd
import numpy as np
np.warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt 
plt.get_backend()
from pymongo import MongoClient
from prettytable import PrettyTable
from statsmodels.tsa.arima_model import ARMA
from sklearn.svm import SVR

def main_menu():    #function prints the menu on the screen and returns inputted value   print('Choose one of the following numbered options\n')
    number = '0'
    x = ['1','2','3','4']
    while number not in x:
        print('1. Trade\n')
        print('2. Blotter\n')
        print('3. Show P/L\n')
        print('4. Quit\n')
        number = input('Input the Number ')  
    return(int(number))

def buy_sell_menu():   #function to ask user if he/she wants to buy or sell
    number = '0'
    x = ['1','2']
    while number not in x:
        print('Would you like to buy or sell?\n')
        print('1. Buy\n')
        print('2. Sell\n')
        number = input('Input the Number ')   
    return(number)
 
#scrapes the names and symbols of all cryptocurrencies from coinmarketcap.com 
def crypto_scraping():  
    url = 'https://coinmarketcap.com/all/views/all/'
    page = urllib.request.urlopen(url)
    soup = bs4.BeautifulSoup(page, 'html.parser') 
     
    crypto_name = soup.find_all("a", class_="currency-name-container")
    name = []
    for item in crypto_name:
        item = item.text.replace(' ','-') #replace space between words with dash so it can access website properly
        name.append(item)
    
    crypto_symbol = soup.find_all("td", class_= "text-left col-symbol")
    symbol=[]
    for item in crypto_symbol:
        symbol.append(item.text)
    
    crypto_df = pd.DataFrame({'name':name, 'symbol':symbol})
    return(crypto_df)    

#user chooses the cryptocurrency to trade    
def trade(crypto_df): 
    print('You may choose any cryptocurrency.  Here is a sample list.\n')
    print(crypto_df.head(7))
    trade_sym = ''
    while trade_sym not in crypto_df['symbol'].values:  #user chooses a cryptocurrency
        trade_sym = input('Give the symbol of the cryptocurrency you would like to trade \n')
        trade_sym = trade_sym.upper()
    row_num = crypto_df[crypto_df['symbol'] == trade_sym].index.tolist()
    print('You chose ' + crypto_df['name'][row_num[0]])
    return(row_num[0]) #return row number of cryptocurrency chosen

#graphs price of chosen cryptocurrency for the last 100 days
def price_chart(row_num, crypto_df):
    #time stamp
    today = datetime.datetime.now()
    DD = datetime.timedelta(days=100)
    earlier = today - DD
    today = today.strftime('%Y%m%d')
    earlier_100days = earlier.strftime('%Y%m%d')

    name = crypto_df['name'][row_num]
    url = 'https://coinmarketcap.com/currencies/'+name+'/historical-data/?start='+earlier_100days+'&end='+today
    page = urllib.request.urlopen(url)
    soup = bs4.BeautifulSoup(page, 'html.parser') 
    
    cost_100days = soup.find_all("tr", class_="text-right")
    
    date = []
    open_cost = []
    if len(cost_100days) < 100:
        print('There are less than 100 days of historical data for ' + name +'\n')
    print('Chart of Price in US Dollars for ' + name + '\n')
    for i in range(len(cost_100days)):      
        datenum = (cost_100days[i].text).split('\n')[1]
        datenum = parser.parse(datenum)
        date.append(datenum)
        open_cost.append(float((cost_100days[i].text).split('\n')[2]))
        cost = pd.Series(open_cost, date)
    print('  Date    Cost in US Dollars at 12am')
    pd.set_option('display.max_rows', len(cost))
    print(cost)

    input('Press enter to view a graph of price in US Dollars for ' + name + ' for the last 100 days\n')
    plt.scatter(x=date,y=open_cost, s= 7)
    plt.gcf().autofmt_xdate()
    dates = date[::10]
    plt.xticks(dates, rotation=60)
    yspacing = np.linspace(min(open_cost), max(open_cost), 10)
    plt.yticks(yspacing)
    plt.title('Cost of ' + name + ' For the Last 100 Days')
    plt.xlabel('Date')
    plt.ylabel('Cost in US Dollars at 12 am')
    plt.tight_layout()
    plt.show(block=True)

    input('Press enter to view a graph of the 20 day moving avearge for ' + name +'\n')  
    rollmean = cost.rolling(window=20).mean()
    plt.plot(rollmean, 'green')
    plt.gcf().autofmt_xdate()
    plt.xticks(dates, rotation=60)
    yspacing = np.linspace(min(open_cost), max(open_cost), 10)
    plt.yticks(yspacing)
    plt.title('20 Day Moving Windown Average for ' + name)
    plt.xlabel('Date')
    plt.ylabel('Cost in US Dollars at 12 am')
    plt.tight_layout()
    plt.show(block=True)

    #collect data and print statistics of last 24 hours from cryptocompare.com API
    symbol = crypto_df['symbol'][row_num]
    url = 'https://min-api.cryptocompare.com/data/histominute?fsym='+symbol+'&tsym=USD&limit=1440'
    page = urllib.request.urlopen(url)
    dailyvalues = json.load(page)
    openval = []
    for item in dailyvalues['Data']:
        openval.append(item['open'])
    sd_val = round(np.std(openval),2)
    max_val = max(openval)
    min_val = min(openval)
    mean_val = round(np.mean(openval),2)
    input('Press enter to view the statistics for the last 24 hours \n')
    table = PrettyTable(["Mean","Minimum Value", "Maximum Value", "Standard Deviation"])
    table.add_row([mean_val,min_val,max_val,sd_val])
    print(table)

#scrapes bid or ask price from bittrex 
#if cryptocurrency price isn't available from bittrex, current price is scraped from coinmarketcap.com for bid and ask
def price_scrape(symbol,side, name):
     url ='https://bittrex.com/api/v1.1/public/getticker?market=usdt-'+symbol
     page = urllib.request.urlopen(url)
     value = json.load(page)
     if value['success']==True:
         price = round(value['result'][side],2)
     else:
         url = 'https://coinmarketcap.com/currencies/' + name
         page = urllib.request.urlopen(url)
         soup = bs4.BeautifulSoup(page, 'html.parser') 
         price = soup.find("span", id="quote_price")
         price = price.text.split('\n')[1]
         price = float(price)
     return(price)
    
#asking user how many dollars he/she wants to purchase, scrapes the current price and conducts the buy
def buy(row_num, crypto_df, cash, blotter2):
     name = crypto_df['name'][row_num]
     symbol = crypto_df['symbol'][row_num]
     dollars = -1
     while True & (dollars <= 0):     
        try:
            dollars = float(input('How many dollars worth of ' + name + ' do you want to purchase?\n'))
            if cash < dollars:
                print('You do not have enough money for this purchase.\n')
        except ValueError:
            print('Choose a number')
            continue
     
     price = price_scrape(symbol,'Ask',name)
          
     timenow = datetime.datetime.now()
     timenow = timenow.strftime('%m-%d-%Y %H:%M:%S')
     
     print('The price of 1 ' + name + ' is $' + str(price) + '\n')
     
     confirm = confirmation()
     if confirm == 0:
         return(cash)
     
     shares_buy = dollars/price
     shares_buy = round(shares_buy,2)
     cash = cash - dollars   
     if blotter2.find({'Ticker':symbol}).count()==0:
         position = shares_buy
         wap = price
         rpl = 0
     else:
         for item in blotter2.find({'Ticker':symbol}):
             lastposition = item['Position']
             wap = item['WAP']
             rpl = item['RPL']
         position = lastposition + shares_buy
         wap  = (wap*lastposition + shares_buy*price)/(lastposition+shares_buy)
         wap = round(wap,2)
     
     post = {"cash": cash, 
             "Side": "Buy", 
             "Ticker": crypto_df['symbol'][row_num], 
             "Quantity": shares_buy, 
             "Executed Price": price, 
             "Timestamp": timenow, 
             "Money In/Out":dollars,
             "Position": position,
             "WAP": wap,
             "RPL": rpl}
 
     blotter2.insert_one(post) 
     return(cash)    
    
#asking user how many dollars worth of cryptocurrency he/she wants to sell, scrapes the current price and conducts the sell
def sell(row_num, crypto_df, cash, blotter2):
     name = crypto_df['name'][row_num]
     symbol = crypto_df['symbol'][row_num]

     dollars = -1
     while True & (dollars <= 0):     
        try:
            dollars = float(input('How many dollars worth of ' + name + ' do you want to sell?\n'))
        except ValueError:
            print('Choose a number')
            continue

     price = price_scrape(symbol,'Bid',name)          
     timenow = datetime.datetime.now()
     timenow = timenow.strftime('%m-%d-%Y %H:%M:%S')
     
     print('The price of 1 ' + name + ' is $' + str(price) + '\n')
 
     share_sell = dollars/price
     share_sell = round(share_sell,2)
     
#check if user position in the coin is greater than the amount user is trying to sell
     if blotter2.find({'Ticker':symbol}).count()==0:
         lastposition = 0
     else:
         for item in blotter2.find({'Ticker':symbol}):
             lastposition = item['Position']
             wap = float(item['WAP'])
#position is less than amount of shares trying to sell   
     if (lastposition==0) | (lastposition < share_sell):
         print('You do not currently have '+ str(share_sell) + ' shares of ' + name + '\n')
         print('You therefore cannot sell ' + name + '\n')
         return(cash)
#user has enough shares to sell - sale goes through
     else:
         cash = cash + dollars
         position = lastposition - share_sell
         rpl = share_sell*(price-wap)
         rpl = round(rpl,2)
                 
         post = {"cash": cash, 
                 "Side": "Sell", 
                 "Ticker": symbol, 
                 "Quantity": share_sell, 
                 "Executed Price": price, 
                 "Timestamp": timenow, 
                 "Money In/Out":dollars,
                 "Position": position,
                 "RPL": rpl,
                 "WAP": wap}
 
         blotter2.insert_one(post) 
         return(cash)


#function to confirm if user wants to buy 
def confirmation():  
    choice = ["Y","N"]
    confirm="A"
    while (confirm not in choice):
        confirm = input("Are you still interested in buying this cryptocurrency? Input Y/N\n")
        confirm = confirm.upper()
    if confirm =="Y":
        print('You chose to buy the cryptocurrency.\n')
        return(1)
    else:
        print('You chose not to go ahead with the buy.\n')
        return(0)

#prints blotter
def print_blotter(blotter2):
    table = PrettyTable(["Cash", "Side", "Ticker", "Quantity", "Executed Price", "Timestamp", "Money In/Out"]) 

    for item in blotter2.find():
        table.add_row([item['cash'],item['Side'],item['Ticker'],item['Quantity'],item['Executed Price'],item['Timestamp'],item['Money In/Out']])
    print(table)

def machinelearning(prediction):
    prediction.delete_many({})
    
    today = datetime.datetime.now()    
    todaydash = today.strftime('%Y-%m-%d')
    DY = datetime.timedelta(days=730)
    earlier = today - DY
    today = today.strftime('%Y%m%d')
    earlier_2years = earlier.strftime('%Y%m%d')

    name = ['Ethereum','Litecoin']
    for item in name:
        url = 'https://coinmarketcap.com/currencies/'+item+'/historical-data/?start='+earlier_2years+'&end='+today
        page = urllib.request.urlopen(url)
        soup = bs4.BeautifulSoup(page, 'html.parser') 
        cost_2years = soup.find_all("tr", class_="text-right")
    
        date = []
        open_cost = []
        for i in range(len(cost_2years)):
            datenum = (cost_2years[i].text).split('\n')[1]
            datenum = parser.parse(datenum)
            date.append(datenum)
            open_cost.append(float((cost_2years[i].text).split('\n')[2]))
    
        today_open = open_cost.pop(0)   
        date.pop(0)
        cost = pd.DataFrame(open_cost, date)
        cost.columns = ['Price at 12am']
        cost.index.name='Date'
            
    #sort data in ascending order
        sorting = cost.index.sort_values(ascending=True)
        cost2 = cost.reindex(sorting)
                
        chg_cost=cost2.diff(7)
        chg_cost=chg_cost.dropna()
    
    #ARMA model               
        mod = ARMA(chg_cost, order=(8,1))
        result = mod.fit()
        forecast = result.forecast()[0]
        invert = len(cost2)-8
        prediction_arma = forecast + cost2.iloc[invert,0]
 
    #Support Vector Machine RBF Model    
        b=np.array(range(0,len(open_cost)))
        b=b.reshape(-1,1)
        svr_rbf=SVR(kernel='rbf',C=1e3,gamma=.05)
        svr_rbf.fit(b,cost2)
        svrrbf = svr_rbf.predict(len(cost2)+1)[0]

        post = {'Name':item,
                'arma':round(prediction_arma[0],2),
                'svrrbf':round(svrrbf,2),
                'todayopen':today_open,
                'date': todaydash}
          
        prediction.insert_one(post) 
              

#print profit/loss table 
def profit_loss(blotter2, crypto_df, prediction,totalpl):
#print predictions
    table = PrettyTable(["Crypto", "ARMA Prediction", "SVM RBF Prediction", "Today's Date", "Price in Dollars at 12am"]) 

    for item in prediction.find():
        table.add_row([item['Name'],item['arma'],item['svrrbf'],item['date'],item['todayopen']])
    print(table)

    if blotter2.count()==0:
        return()
    pl_df = pd.DataFrame()
#Find the total quantity of shares owned: Total shares = total shares bought-total shares sold
    total_shares = list(blotter2.aggregate([{"$group":
          {"_id" : {"Side": "$Side"},
                    "Total":  {"$sum": "$Quantity"}}} ] ))

#Find the total dollars of shares owned: Total dollars = total dollars for coins bought-total dollars of coins sold    
    total_dollars = list(blotter2.aggregate([{"$group":
          {"_id" : {"Side": "$Side"},
                    "Total":  {"$sum": "$Money In/Out"}}} ] ))
#Check if shares have been bought and sold    
    if len(total_shares)==2:
        total_shares = total_shares[1]['Total']-total_shares[0]['Total']
        total_dollars = total_dollars[1]['Total']-total_dollars[0]['Total']
    else:
        total_shares = total_shares[0]['Total']
        total_dollars = total_dollars[0]['Total']

#identify all distinct cryptocurrencies bought and sold
    tickerlist = blotter2.distinct('Ticker')
    for item in tickerlist:
        name = crypto_df[crypto_df['symbol'] == item]['name'].tolist()[0]

        for value in blotter2.find({'Ticker':item}):
            lastposition = round(value['Position'],2)
            wap = value['WAP']
            rpl = value['RPL']
        
        price = price_scrape(item,'Bid',name)
     
        upl = (price-wap)*lastposition
        upl = round(upl,2)
        totpl = rpl + upl
        totpl = round(totpl,2)

#determine the amount of money invested in a particular cryptocurrency
        crypto_dollars = list(blotter2.aggregate([
                {"$match": {"Ticker": item}},
                {"$group": {"_id" : {"Side": "$Side"},
                    "Total":  {"$sum": "$Money In/Out"}}} ] ))
        if len(crypto_dollars)==2:
            crypto_dollars = crypto_dollars[1]['Total'] - crypto_dollars[0]['Total']    
        else:
            crypto_dollars = crypto_dollars[0]['Total']
            
        alloc_shares = round(lastposition*100/total_shares,2)
        alloc_dollars = round(crypto_dollars*100/total_dollars,2)
       
        pl_df = pl_df.append({'Ticker':item,
                      'Position':lastposition,
                      'Current Price':price,
                      'WAP':wap,
                      'UPL':upl,
                      'RPL':rpl,
                      'Total P/L':totpl,
                      'Alloc By Shares':alloc_shares,
                      'Alloc By Dollars':alloc_dollars}, ignore_index=True)
  
    post = {'tpl':sum(pl_df['Total P/L']),
           'date':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    totalpl.insert_one(post)

    sum(pl_df['Total P/L'])    
    
    table = PrettyTable([''] + list(pl_df.columns))
    for row in pl_df.itertuples():
        table.add_row(row)
    print(table)
 
    
    
#Find cash on hand To Graph Cash as a Function of Time
    cash_df = pd.DataFrame()
    for item in blotter2.find():
        cash_df = cash_df.append({'cash':item['cash'],
                                  'time':item['Timestamp']}, ignore_index=True)
    
    input('Press enter to view a graph of cash on hand. \n')
    plt.scatter(x=cash_df['time'],y=cash_df['cash'], s= 7)
    plt.gcf().autofmt_xdate()
    dates = cash_df['time']
    plt.xticks(dates, rotation=60)
    yspacing = np.linspace(min(cash_df['cash']), max(cash_df['cash']), 10)
    plt.yticks(yspacing)
    plt.title('Cash on Hand as a Function of Time')
    plt.xlabel('Date')
    plt.ylabel('Cash in Dollars')
    plt.tight_layout()
    plt.show(block=True)

#Graph Total Portfolio (RPL+UPL) as a Function of Time
    tot_df = pd.DataFrame()
    for item in totalpl.find():
        tot_df = tot_df.append({'totpl':item['tpl'],
                                  'time':item['date']}, ignore_index=True)
    
    input('Press enter to view a graph of cash on hand. \n')
    plt.scatter(x=tot_df['time'],y=tot_df['totpl'], s= 7)
    plt.gcf().autofmt_xdate()
    dates = tot_df['time']
    plt.xticks(dates, rotation=60)
    yspacing = np.linspace(min(tot_df['totpl']), max(tot_df['totpl']), 10)
    plt.yticks(yspacing)
    plt.title('Total Portfolio as a Function of Time')
    plt.xlabel('Date')
    plt.ylabel('Total Portfolio')
    plt.tight_layout()
    plt.show(block=True)

#Graph VWAP and Executed Price History for 1 Crypto
    tickerval = tickerlist[0]
    wap_df = pd.DataFrame()
    for value in blotter2.find({'Ticker':tickerval}):
        wap_df = wap_df.append({'wap':value['WAP'],
                            'exec_price':value['Executed Price'],    
                            'time':value['Timestamp']}, ignore_index=True)
   
    input('Press enter to view a graph of Weighted Average Price. \n')
    plt.scatter(x=wap_df['time'],y=wap_df['wap'], s= 7)
    plt.gcf().autofmt_xdate()
    dates = wap_df['time']
    plt.xticks(dates, rotation=60)
    yspacing = np.linspace(min(wap_df['wap']), max(wap_df['wap']), 10)
    plt.yticks(yspacing)
    plt.title('Weighted Average Price For '+ tickerval +' as a Function of Time')
    plt.xlabel('Date')
    plt.ylabel('Weighted Average Price in Dollars')
    plt.tight_layout()
    plt.show(block=True)    

    input('Press enter to view a graph of Executed Price. \n')
    plt.scatter(x=wap_df['time'],y=wap_df['exec_price'], s= 7)
    plt.gcf().autofmt_xdate()
    dates = wap_df['time']
    plt.xticks(dates, rotation=60)
    yspacing = np.linspace(min(wap_df['exec_price']), max(wap_df['exec_price']), 10)
    plt.yticks(yspacing)
    plt.title('Executed Price For '+ tickerval +' as a Function of Time')
    plt.xlabel('Date')
    plt.ylabel('Executed Price in Dollars')
    plt.tight_layout()
    plt.show(block=True) 


    
def main():
    print("Please be patient while the program runs prediction models...\n")
    MONGO_URI = "mongodb://test:test@ds113000.mlab.com:13000/wigdb"
    client = MongoClient(MONGO_URI, connectTimeoutMS = 30000) 
    db = client.get_database()
    blotter2 = db.blotter2
    prediction = db.prediction
    totalpl = db.totalpl
    machinelearning(prediction)
    if blotter2.count()==0:
        cash = 100000000
    else:
        count = blotter2.count()
        cash = blotter2.find()[count-1]['cash']

    crypto_df = crypto_scraping()

    choice = 5
    while choice != 4:
        choice = main_menu()
    
        if choice == 1:
            row_num = trade(crypto_df)
            price_chart(row_num, crypto_df)
            buysell = buy_sell_menu()
            if buysell == '1':
                cash = buy(row_num, crypto_df, cash, blotter2)
            else:
                cash = sell(row_num, crypto_df, cash, blotter2)

        elif choice == 2:
            print_blotter(blotter2)
        
        elif choice == 3:
            profit_loss(blotter2, crypto_df, prediction,totalpl)
    return()    

if __name__ == "__main__":
    main()        