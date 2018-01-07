from flask import render_template, request, redirect
from app import app
from app.utils import format_price
from enum import Enum

import requests
import json
import datetime

# get the API Key from the config file
apiKey = app.config["API_KEY"]

# http://www.davidadamojr.com/handling-cors-requests-in-flask-restful-apis/
@app.after_request
def after_request(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
	response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
	return response



# ========== UPDATE BELOW THIS LINE ========== #



# This route loads the home screen.  Get all data necessary and pass it to the view. 
@app.route('/')
@app.route('/index')
def index():
    accountsUrl = 'http://api.reimaginebanking.com/accounts?key={}'.format(apiKey)
    accountsResponse = requests.get(accountsUrl)
    # if the accounts call responds with success
    if accountsResponse.status_code == 200:
        accounts = json.loads(accountsResponse.text)
        
        # filter out any credit card accounts (can't transfer money to/from them)
        accountsNoCards = []
        transfers = []

        for account in accounts:
            if account["type"] != "Credit Card":
                accountsNoCards.append(account);
                url = "http://api.reimaginebanking.com/accounts/{}/transfers?key={}".format(account["_id"], apiKey)
                transfer = requests.get(url)
                datalist = json.loads(transfer.text)

                for data in datalist:
                    transfers.append(data)

        return render_template("home.html", accounts=accounts, transfers=transfers, format_price=format_price)
    else:
        return render_template("notfound.html")



# This route should get the fields from the form and create a transfer POST request
@app.route('/transfer', methods=['POST'])
def postTransfer():
    fromAccount = request.form["fromAccount"]
    if fromAccount == "":
        return redirect("/index", code=302)
    
    toAccount = request.form["toAccount"]
    if toAccount == "":
        return redirect("/index", code=302)

    try:
        amount = float(request.form["amount"]) # need to convert to an int or this fails
    except ValueError:
        amount = ""

    description = request.form["description"]
    medium = "balance";
    dateObject = datetime.date.today()
    dateString = dateObject.strftime('%Y-%m-%d')
    body = {
        'medium' : medium,
        'payee_id' : toAccount,
        'amount' : amount,
        'transaction_date' : dateString,
        'description' : description
    }
    url = "http://api.reimaginebanking.com/accounts/{}/transfers?key={}".format(fromAccount, apiKey)
    response = requests.post(
                         url,
                         data=json.dumps(body),
                         headers={'content-type':'application/json'})

    print(response.text)

    # redirect user to the same page, which should now show there latest transaction in the list
    return redirect("/index", code=302)



