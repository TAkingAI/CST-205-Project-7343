
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

storedaily = {}

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

def reduceToOneDiff(data):
    diff = 0.0
    numDays = 0
    for key in data:
        diff+=data[key]
        numDays+=1
    
    try:
        return round(diff/numDays, 2)
    except:
        return 0.0
    

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

def groupByDay(data):
    weekdays = ["Friday", "Thursday", "Wednesday", "Tuesday", "Monday"]
    newdata = {}
    for day in weekdays:
        newdata[day] = reduceToOneDiff(limitSpecificWeekday(day, data))

    return newdata

def limitSpecificMonth(month, data):
    newdata = {}
    for key in data:
        ymd = key.split("-")
        if ((datetime.datetime(int(ymd[0]), int(ymd[1]), int(ymd[2]))).strftime("%b") == month):
            newdata[key] = data[key]
    return newdata

def groupByMonth(data):
    months = ["Dec", "Nov", "Oct", "Sep", "Aug", "Jul", "Jun", "May", "Apr", "Mar", "Feb", "Jan"]
    newdata = {}
    for month in months:
        newdata[month] = reduceToOneDiff(limitSpecificMonth(month, data))

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

@app.route('/')
def start():
    return render_template('start.html')

@app.route('/stock/<symbol>')
def stock(symbol):
    try:
        now = datetime.date.today()
        today = now.strftime('%Y-%m-%d')
        lastWeek = (now + dateutil.relativedelta.relativedelta(weeks=-1)).strftime('%Y-%m-%d')
        lastMonth = (now + dateutil.relativedelta.relativedelta(months=-1)).strftime('%Y-%m-%d')
        lastYear = (now + dateutil.relativedelta.relativedelta(years=-1)).strftime('%Y-%m-%d')
        last5Year = (now + dateutil.relativedelta.relativedelta(years=-5)).strftime('%Y-%m-%d')

        intraday = getApiData('TIME_SERIES_INTRADAY', symbol)
        daily = getApiData('TIME_SERIES_DAILY', symbol)
        storedaily[symbol] = daily
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
        
        data = {'intraday': intradaydata , 'week': weekdata, 'month': monthdata, 'year': yeardata, 'fiveyears': fiveyeardata, 'max': maxdata, 'overview': overviewdata, 'incomestatements': incomestatementsdata }
        return render_template('stock.html', overview = overview, data = data, symbol = symbol)
    except:
        return render_template('notAvailable.html')
   
@app.route('/chart/<symbol>/<startdate>/<enddate>/<group>')
def chart(symbol, startdate, enddate, group):
    daily = {}
    try:
        daily = storedaily[symbol]
    except:
        daily = getApiData('TIME_SERIES_DAILY', symbol)
    
    data = limitDateRange(startdate, enddate, daily['Time Series (Daily)'] )
    charttype = ""
    if group=="day":
        data = getChartData(groupByDay(reduceToDiff((data))))
        charttype = "bar"
    elif group == "month":
        data = getChartData(groupByMonth(reduceToDiff((data))))
        charttype = "bar"
    elif group == "none":
        data = getChartData(reduceToCloseValue((data)))
        charttype = "line"

    return render_template('chart.html',  data = {'data': data}, charttype= charttype, symbol=symbol, startdate=startdate, enddate=enddate )


@app.route('/notFound')
def notAvailable():
    return render_template('notAvailable.html')
