
# Author:Tobias Alt
# CST 205 Multimedia Programming and Design
# Project Stock Data Analyzer
# Projectnumber 7343
# May 20, 2022
# GitHub: 

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

#API endpoint and keys
endpoint = 'https://www.alphavantage.co/query?'
my_key = 'DSEC20YGZLK3JE12'

#data storage while server running
datastore = {}


# calling API with key
def getApiData(function, symbol):
    request = endpoint + f'function={function}&symbol={symbol}'
    if function=="TIME_SERIES_INTRADAY":
        request += '&interval=5min'
        
    elif function=="TIME_SERIES_DAILY":
        request += '&outputsize=full'
    
    request += f'&apikey={my_key}'
    response = requests.get(request)
    return response.json()


#calculate difference between stock prices (open and close value)
def calculateDiff(day):
    return (float(day['1. open'])-float(day['4. close'])) / float(day['1. open'])

#reduce data to diff data
def reduceToDiff(data):
    newdata = {}
    for key in data:
        newdata[key] = round(calculateDiff(data[key])*100, 2)
    return newdata

#reduce data to one diff value
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
    
#reduce data to close stock price data
def reduceToCloseValue(data):
    newdata = {}
    for key in data:
        newdata[key] = float(data[key]['4. close'])
    return newdata

#reduce data to specific time period
def reduceTimePeriod(startdate, enddate, data):
    newdata = {}
    for key in data:
        if (key >= startdate and key<= enddate):
            newdata[key] = data[key]
    return newdata

#reduce data to specific weekday 
def reduceWeekday(day, data):
    newdata = {}
    for key in data:
        ymd = key.split("-")
        if ((datetime.datetime(int(ymd[0]), int(ymd[1]), int(ymd[2]))).strftime("%A") == day):
            newdata[key] = data[key]
    return newdata

#group data by weekdays
def groupByWeekdays(data):
    weekdays = ["Friday", "Thursday", "Wednesday", "Tuesday", "Monday"]
    newdata = {}
    for day in weekdays:
        newdata[day] = reduceToOneDiff(reduceWeekday(day, data))

    return newdata

#reduce Data to specific month
def reduceMonth(month, data):
    newdata = {}
    for key in data:
        ymd = key.split("-")
        if ((datetime.datetime(int(ymd[0]), int(ymd[1]), int(ymd[2]))).strftime("%b") == month):
            newdata[key] = data[key]
    return newdata

#groyp data by months
def groupByMonths(data):
    months = ["Dec", "Nov", "Oct", "Sep", "Aug", "Jul", "Jun", "May", "Apr", "Mar", "Feb", "Jan"]
    newdata = {}
    for month in months:
        newdata[month] = reduceToOneDiff(reduceMonth(month, data))

    return newdata

def splitKeyName(data):
    newdata = {}
    for key in data:
        newdata[key.split()[1]] = data[key]
    return newdata


#modify data for graphjs
def getChartData(data):
    newdata = {'labels': [], 'data': []}
    for key in data:
        newdata['labels'].append(key)
        newdata['data'].append(data[key])
    newdata['labels'].reverse()
    newdata['data'].reverse()
    return newdata

#modify overview data  
def modifyOverview(data):
    newdata = data
    newdata['MarketCapitalization'] =  numerize.numerize(int(newdata['MarketCapitalization']))
    return newdata

#modify income statement data
def modifyIncomeStatement(data):
    newdata = data
    for statement in range(len(data)):
        newdata[statement]['totalRevenue'] = numerize.numerize(int(newdata[statement]['totalRevenue']))
        newdata[statement]['ebit'] = numerize.numerize(int(newdata[statement]['ebit']))
        newdata[statement]['incomeBeforeTax'] = numerize.numerize(int(newdata[statement]['incomeBeforeTax']))
        newdata[statement]['netIncome'] = numerize.numerize(int(newdata[statement]['netIncome']))

    return newdata


# create an instance of Flask
app = Flask(__name__)
bootstrap = Bootstrap5(app)

#render start template
@app.route('/')
def start():
    return render_template('start.html')

#render stock template
@app.route('/stock/<symbol>')
def stock(symbol):
    try:
        #define time variables
        now = datetime.date.today()
        today = now.strftime('%Y-%m-%d')
        lastWeek = (now + dateutil.relativedelta.relativedelta(weeks=-1)).strftime('%Y-%m-%d')
        lastMonth = (now + dateutil.relativedelta.relativedelta(months=-1)).strftime('%Y-%m-%d')
        lastYear = (now + dateutil.relativedelta.relativedelta(years=-1)).strftime('%Y-%m-%d')
        last5Year = (now + dateutil.relativedelta.relativedelta(years=-5)).strftime('%Y-%m-%d')

        #get api data
        intraday = getApiData('TIME_SERIES_INTRADAY', symbol)
        daily = getApiData('TIME_SERIES_DAILY', symbol)
        datastore[symbol] = daily
        monthly = getApiData('TIME_SERIES_MONTHLY', symbol)
        overview = getApiData('OVERVIEW', symbol)
        #balancesheets = getApiData('BALANCE_SHEET', symbol)
        incomestatements = getApiData('INCOME_STATEMENT', symbol)

        #prepare data before pass to template
        intradaydata = getChartData(splitKeyName(reduceToCloseValue(intraday['Time Series (5min)'])))
        weekdata = getChartData(reduceToCloseValue(reduceTimePeriod(lastWeek, today, daily['Time Series (Daily)'] )))
        monthdata = getChartData(reduceToCloseValue(reduceTimePeriod(lastMonth, today, daily['Time Series (Daily)'] )))
        yeardata = getChartData(reduceToCloseValue(reduceTimePeriod(lastYear, today, monthly['Monthly Time Series'] )))
        fiveyeardata = getChartData(reduceToCloseValue(reduceTimePeriod(last5Year, today, monthly['Monthly Time Series'] )))
        maxdata = getChartData(reduceToCloseValue(monthly['Monthly Time Series']))
        overviewdata = modifyOverview(overview)
        #balancesheetsdata = balancesheets['annualReports']
        incomestatementsdata =  modifyIncomeStatement(incomestatements['annualReports'])
        
        data = {'intraday': intradaydata , 'week': weekdata, 'month': monthdata, 'year': yeardata, 'fiveyears': fiveyeardata, 'max': maxdata, 'overview': overviewdata, 'incomestatements': incomestatementsdata }
        return render_template('stock.html', overview = overview, data = data, symbol = symbol)
    except:
        return render_template('notAvailable.html')

#render advanced option chart template
@app.route('/chart/<symbol>/<startdate>/<enddate>/<group>')
def chart(symbol, startdate, enddate, group):
    daily = {}
    try:
        daily = datastore[symbol]
    except:
        daily = getApiData('TIME_SERIES_DAILY', symbol)
    
    data = reduceTimePeriod(startdate, enddate, daily['Time Series (Daily)'] )
    charttype = ""
    if group=="day":
        data = getChartData(groupByWeekdays(reduceToDiff((data))))
        charttype = "bar"
    elif group == "month":
        data = getChartData(groupByMonths(reduceToDiff((data))))
        charttype = "bar"
    elif group == "none":
        data = getChartData(reduceToCloseValue((data)))
        charttype = "line"

    return render_template('chart.html',  data = {'data': data}, charttype= charttype, symbol=symbol, startdate=startdate, enddate=enddate )

#render notAvailable template
@app.route('/notFound')
def notAvailable():
    return render_template('notAvailable.html')
