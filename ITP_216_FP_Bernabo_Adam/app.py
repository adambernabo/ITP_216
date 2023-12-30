"""
Adam Bernabo, bernabo@usc.edu
ITP 216, Spring 2023, Section: 31885
Final Project

NOTES: data set was retrieved from Kaggle
(https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks?select=sp500_stocks.csv) although it seems to be not working
since I downloaded it. Also, data is taken from the first of each month for each company, so when picking a day for
visualizing volumes, the user must always pick the first of the month (input must always be mm/01/yyy). Data when I
got it was from 01/01/2018 to 03/01/2023

A Final note: I was not able to successfully implement the ML aspect of the project, so I took a different route for
the "meaningful aggregation" and second POST requirements of the project (moving volume visualization)

PS: Thank you for a great semester! I'm not a CS major, but had an interest in programming. This course has only fueled
that interest. All the best.
"""
from flask import Flask, redirect, render_template, request, session, url_for, send_file
import os
import io
import sqlite3 as sl
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = "sp500_prices.db"


# Home page. Houses the options for data usage
@app.route("/")
def home():

    options = {
        "Historical Data (2018-2022)": "Historical Data (2018-2022)",
        "Highs and Lows in 2023": "Highs and Lows in 2023"
        }
    return render_template("home.html", tickers=db_get_tickers(), message="Please enter a ticker to search for.",
                           options=options)


# POST method that gets the user's selected ticker and the data_request
@app.route("/submit_ticker", methods=["POST"])
def submit_ticker():
    print(request.form['ticker'])
    session['ticker'] = request.form['ticker']
    # if there is no session ticker, redirected back home
    if 'ticker' not in session or session['ticker'] == "":
        return redirect(url_for('home'))
    if "data_request" not in request.form:
        return redirect(url_for("home"))
    session['data_request'] = request.form['data_request']
    # redirected to see data otherwise
    return redirect(url_for('ticker_current', data_request=session['data_request'], ticker=session['ticker']))


@ app.route('/api/stockdata/<data_request>/<ticker>')
def ticker_current(data_request, ticker):
    return render_template('ticker.html', data_request=data_request, ticker=ticker, volume=False)


@app.route("/submit_volume", methods=["POST"])
def submit_volume():
    # if no session ticker, redirected back home
    if 'ticker' not in session:
        return redirect(url_for("home"))
    session["date"] = request.form["date"]
    # print(session['date'])
    # also redirected home if session ticker, data request, or date is null
    if session["ticker"] == "" or session["data_request"] == "" or session["date"] == "":
        return redirect(url_for("home"))

    # otherwise, redirected for volume visualization
    return redirect(url_for("volume_visualization", data_request=session["data_request"], ticker=session["ticker"]))


# if everything is valid, brought back to ticker but with a valid date token which visualizes volume
@app.route("/api/stockdata/<data_request>/volume/<ticker>")
def volume_visualization(data_request, ticker):
    return render_template("ticker.html", data_request=data_request, ticker=ticker, volume=True, date=session["date"])


# takes the figure from the create_figure function and saves as a png to me rendered on the web app
@app.route('/fig/<data_request>/<ticker>')
def fig(data_request, ticker):
    fig = create_figure(data_request, ticker)

    img= io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype='image/png')


#visualizes the data using pyplot
def create_figure(data_request, ticker):
    # month and year lists are used for ticker labels
    month_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    year_list = ['2018', '2019', '2020', '2021', '2022', '2023']

    # a Pandas dataframe is created using the create dataframe function and is used for data visualization
    df = db_create_dataframe(data_request, ticker)
    # print(df)
    # print(session)
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    # if date is not in the session, volume data is not visualized and instead one of the two options using the buttons
    # on the front menu is.
    if 'date' not in session:
        # creates the plot dynamically depending on the data_request
        if data_request == 'Historical':
            fig.suptitle('Daily highs for ' + ticker + ' from 1/1/2018 to 3/1/2023')
            # plots the dates against the daily highs using the dataframe
            ax.plot(df['date_str'], df['High'])
            ax.set(xlabel='year (Jan 1 of every year)', ylabel='daily high (in USD)', xticks=range(0, len(df), 12))
            ax.grid()
            ax.xaxis.set_ticklabels(year_list)
            # print(str(len(df)))
            return fig
        # plots the highs against the lows for a company in the most recent full year (2022)
        elif data_request == 'Highs':
            fig.suptitle(' Highs and lows for ' + ticker + ' in 2022')
            # dataframe is filtered to only include the year 2022
            df_2022 = df[df['Year'] == 2022]
            # the Highs and lows are then plotted against each other
            ax.plot(df_2022['date'], df_2022['High'], label='High')
            ax.plot(df_2022['date'], df_2022['Low'], label='Low')
            ax.set(xlabel='date', ylabel='Price (in USD)')
            ax.grid()
            ax.xaxis.set_ticklabels(month_list)
            ax.legend()
            return fig
    # if there is a session date, a bar graph for the companies with the 5 highest trading volumes is created showing
    # the total of shares traded between the five on that date
    # note: data for this set was collected on the first of each month, so users must input a the first of a month
    # within the data's range. This was just a characteristic of this data set.
    elif 'date' in session:
        fig.suptitle('5 Most Traded Companies on ' + session['date'] + ' totaling '
                     + str(df['Volume'].sum()) + ' shares')
        ax.bar(x=df['Company'], height=df['Volume'])
        ax.set(xlabel='Company Ticker', ylabel='Volume')
        # takes the session date out so that the visualized volume does not plot unexpectedly (this bug took me an hour)
        session.pop('date', None)
        return fig

    plt.tight_layout()
    plt.show()


# data is retrieved from the sp500_prices table of the sp500_prices.db database. This database was created using an
# adopted version of the CSV_to_DB file from the starter code included in the project directory
def db_create_dataframe(data_request, ticker):
    conn = sl.connect(db)
    curs = conn.cursor()

    table = 'sp500_prices'
    print(f'{table=}')
    print(f'{ticker=}')
    # different queries are made depending on if there is a session date
    if 'date' not in session:

        # If there is a session date, queries where the company is equal to the selected ticker
        stmt = "SELECT * FROM " + table + " WHERE `Company`=?"

        data = curs.execute(stmt, (ticker, ))
        results = data.fetchall()

        # proper data hygiene
        curs.close()
        conn.close()

        # query is then turned into a dataframe and returned to be used elsewhere
        df = pd.DataFrame(results, columns=[desc[0] for desc in curs.description])
        return df
    elif 'date' in session:
        # if there is a session date, a query is instead made based on where the date of the row is equal to the session
        # date
        date = (session["date"],)
        # query statement
        stmt = "SELECT * FROM " + table + " WHERE `date_str`=?"

        data = curs.execute(stmt, date)
        results = data.fetchall()

        # again, proper data hygiene
        curs.close()
        conn.close()

        # again the data from the query is then turned into a dataframe
        df = pd.DataFrame(results, columns=[desc[0] for desc in curs.description])

        # sorted by greatest volume
        df_sorted = df.sort_values('Volume', ascending=False)

        # take the top 5
        df_top_five = df_sorted.head(5)
        # print(df_top_five)
        # returned
        return df_top_five


# gets a list of tickers
def db_get_tickers():
    conn = sl.connect(db)
    curs = conn.cursor()

    table = "sp500_prices"
    stmt = 'SELECT `Company` FROM ' + table
    data = curs. execute(stmt)
    # sort set comprehension for unique values from starter code
    tickers = sorted({result[0] for result in data})

    # you already know
    curs.close()
    conn.close()
    # list of tickers is then returned to be picked by the user
    return tickers


# catch all path to redirect back home
@app.route('/<path:path>')
def catch_all(path):
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)



