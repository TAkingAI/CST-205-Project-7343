
# Tobias Alt
# CST 205 Multimedia Programming and Design
# Project
# Projectnumber 7343
# May 19, 2022


from numerize import numerize
from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
import random
from PIL import Image
import requests
import datetime
import dateutil.relativedelta
import pprint
from numerize import numerize

endpoint = 'https://www.alphavantage.co/query?'
my_keys = ['DSEC20YGZLK3JE12', '4146MARPBSQSB99J', 'DXY63PIFFPJVX3FM', '99AB07D80GEJAEJB', '77DVW67VV7G27YLF', 'QQ97SRZ0AAULXKXV' ]

def getRandomApiKey():
    return random.choice(my_keys)

# get html site
def getApiData(function, symbol):
    request = endpoint + f'function={function}&symbol={symbol}'
    if function=="TIME_SERIES_INTRADAY":
        request += '&interval=5min'
        
    elif function=="TIME_SERIES_DAILY":
        request += '&outputsize=full'
    
    request += f'&apikey={getRandomApiKey()}'
    print(request)
    
    try:
        response = requests.get(request)
        #pprint(response.json)
        return response.json()
    except:
        print('error while contacting api')


def splitKeyName(data):
    newdata = {}
    for key in data:
        newdata[key.split()[1]] = data[key]
    return newdata


def calculateDiff(day):
    return (float(day['1. open'])-float(day['4. close'])) / float(day['1. open'])

def reduceToDiff(data):
    newdata = {}
    for key in data:
        newdata[key] = round(calculateDiff(data[key])*100, 2)
    return newdata

def reduceToCloseValue(data):
    newdata = {}
    for key in data:
        newdata[key] = float(data[key]['4. close'])
    return newdata

def limitDateRange(startdate, enddate, data):
    newdata = {}
    for key in data:
        if (key >= startdate and key<= enddate):
            newdata[key] = data[key]
    return newdata

def limitSpecificWeekday(day, data):
    newdata = {}
    for key in data:
        ymd = key.split("-")
        if ((datetime.datetime(int(ymd[0]), int(ymd[1]), int(ymd[2]))).strftime("%A") == day):
            newdata[key] = data[key]
    return newdata


def getChartData(data):
    newdata = {'labels': [], 'data': []}
    for key in data:
        newdata['labels'].append(key)
        newdata['data'].append(data[key])
    newdata['labels'].reverse()
    newdata['data'].reverse()
    return newdata

def modifyOverview(data):
    newdata = data
    newdata['MarketCapitalization'] =  numerize.numerize(int(newdata['MarketCapitalization']))
    return newdata

def modifyIncomeStatement(data):
    newdata = data
    for statement in range(len(data)):
        newdata[statement]['totalRevenue'] = numerize.numerize(int(newdata[statement]['totalRevenue']))
        newdata[statement]['ebit'] = numerize.numerize(int(newdata[statement]['ebit']))
        newdata[statement]['incomeBeforeTax'] = numerize.numerize(int(newdata[statement]['incomeBeforeTax']))
        newdata[statement]['netIncome'] = numerize.numerize(int(newdata[statement]['netIncome']))

    return newdata


def getAnnualData(data):
    return data

#round(getDiff(data[key])*100, 2)



# create an instance of Flask
app = Flask(__name__)
bootstrap = Bootstrap5(app)

# route decorator binds a function to a URL
# start random images site
@app.route('/')
def randomImages():
    today = datetime.date.today()
    lastMonth = today + dateutil.relativedelta.relativedelta(weeks=-1)
    return (lastMonth.strftime('%Y-%m-%d'))


@app.route('/stock/<symbol>')
def stockSite(symbol):
    #try:
        now = datetime.date.today()
        today = now.strftime('%Y-%m-%d')
        lastWeek = (now + dateutil.relativedelta.relativedelta(weeks=-1)).strftime('%Y-%m-%d')
        lastMonth = (now + dateutil.relativedelta.relativedelta(months=-1)).strftime('%Y-%m-%d')
        lastYear = (now + dateutil.relativedelta.relativedelta(years=-1)).strftime('%Y-%m-%d')
        last5Year = (now + dateutil.relativedelta.relativedelta(years=-5)).strftime('%Y-%m-%d')

        intraday = getApiData('TIME_SERIES_INTRADAY', symbol)
        daily = getApiData('TIME_SERIES_DAILY', symbol)
        monthly = getApiData('TIME_SERIES_MONTHLY', symbol)
        overview = getApiData('OVERVIEW', symbol)
        #balancesheets = getApiData('BALANCE_SHEET', symbol)
        incomestatements = getApiData('INCOME_STATEMENT', symbol)

        intradaydata = getChartData(splitKeyName(reduceToCloseValue(intraday['Time Series (5min)'])))
        weekdata = getChartData(reduceToCloseValue(limitDateRange(lastWeek, today, daily['Time Series (Daily)'] )))
        monthdata = getChartData(reduceToCloseValue(limitDateRange(lastMonth, today, daily['Time Series (Daily)'] )))
        yeardata = getChartData(reduceToCloseValue(limitDateRange(lastYear, today, monthly['Monthly Time Series'] )))
        fiveyeardata = getChartData(reduceToCloseValue(limitDateRange(last5Year, today, monthly['Monthly Time Series'] )))
        maxdata = getChartData(reduceToCloseValue(monthly['Monthly Time Series']))
        overviewdata = modifyOverview(overview)
        #balancesheetsdata = balancesheets['annualReports']
        incomestatementsdata =  modifyIncomeStatement(incomestatements['annualReports'])
        
        #data = getApiData('TIME_SERIES_DAILY', symbol)
        #diff = reduceToDiff(data['Time Series (Daily)']['2022-04-14'])
        #daterange = limitDateRange("2021-01-08", "2022-04-18", data['Time Series (Daily)'] )
        #diff = reduceToDiff(daterange)
        #closeValues = reduceToCloseValue(daterange)
        #onlyFriday = limitSpecificWeekday('Friday', daterange)
        #onlyFridayDiff = reduceToDiff(onlyFriday)
        #stockdata = getLabels(closeValues)
        
        #data = {'intraday': intradaydata , 'week': weekdata, 'month': monthdata, 'year': yeardata, 'fiveyears': fiveyeardata, 'max': maxdata, 'overview': overviewdata, 'balancesheets': balancesheetsdata, 'incomestatements': incomestatementsdata }
        data = {'intraday': intradaydata , 'week': weekdata, 'month': monthdata, 'year': yeardata, 'fiveyears': fiveyeardata, 'max': maxdata, 'overview': overviewdata, 'incomestatements': incomestatementsdata }
        return render_template('index.html', overview = overview, data = data)
    #except:
    #    return render_template('notAvailable.html')
   

@app.route('/stock')
def example():
    #return render_template('index.html' )
    incomestatements = getApiData('INCOME_STATEMENT', 'IBM')
    incomestatementsdata = incomestatements['annualReports'][0]
    #intraday = getApiData('TIME_SERIES_INTRADAY', "IBM")
    #intradaydata = getChartData(splitKeyName(reduceToCloseValue(intraday['Time Series (5min)'])))

    return incomestatementsdata


@app.route('/notFound')
def notAvailable():
    return render_template('notAvailable.html')