
import sqlite3 as sl
import pandas as pd


pd.set_option('display.max_columns', None)

# Create/Connect database
conn = sl.connect('sp500_prices.db')
curs = conn.cursor()

# Create our table if it doesn't already exist
# Manually specify table name, column names, and columns types
curs.execute('DROP TABLE IF EXISTS sp500_prices')
curs.execute('CREATE TABLE IF NOT EXISTS '
             'sp500_prices (`Company` text, `High` number, `Low` number, `Volume` number, `Year` number, `Month` number, `Day` number)')
conn.commit()  # don't forget to commit changes before continuing

# Use pandas which you already to know to read the csv to df
# Select just the columns you want using optional use columns param
df = pd.read_csv('sp500_prices.csv', usecols=['Company', 'High', 'Low', 'Volume', 'Year', 'Month', 'Day'])
# drop nulls just like pandas hw
df = df[df["High"].notnull()]

# create a mm/dd/yyy formatted column
df['date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
df['date_str'] = df['date'].dt.strftime('%m/%d/%Y')

# read head
print('First 3 df results:')
print(df.head(3))


# Let pandas do the heavy lifting of converting a df to a db
# name=your existing empty db table name, con=your db connection object
# just overwrite if the values already there, and don't index any columns
df.to_sql(name='sp500_prices', con=conn, if_exists='replace', index=False)

# The rest is from the DB lecture and HW
print('\nFirst 3 db results:')
query = 'SELECT * FROM sp500_prices'
results = curs.execute(query).fetchmany(3)
for result in results:
    print(result)

result = curs.execute('SELECT COUNT(*) FROM sp500_prices').fetchone()
# Note indexing into the always returned tuple w/ [0]
# even if it's a tuple of one
print('\nNumber of valid db rows:', result[0])
print('Number of valid df rows:', df.shape[0])

result = curs.execute('SELECT MAX(`High`) FROM sp500_prices').fetchone()
print('Max Observed price', result[0])

# Now go back to a Pandas dataframe from SQL query
# e.g. db_create_dataframe()
df_sql_query = pd.read_sql_query(query, conn)
# Down selecting the columns we want to grab from db to df
df = pd.DataFrame(df_sql_query, columns=['Company', 'High', 'Low', 'Volume', 'date_str'])
print('back to df:\n', df.head(3))

# Plot w/ Pandas abstraction layer over matplotlib
# simply provide the name of columns/series/numpy array wrappers
# Observed Temperature vs Time
# df.plot('Company', 'High')
# call matplotlib plt show() like always
# plt.show()

# Convert date strings to ordinal numbers for ML
# df['DATE_ORD'] = pd.to_datetime(df['DATE'])\
#     .map(datetime.datetime.toordinal).dropna()
# print(df['DATE_ORD'].head(3))
#
# X_train, X_test, y_train, y_test = \
#     train_test_split(df['DATE_ORD'], df['TOBS'],
#                      test_size=0.5, random_state=0)

# Models. Comment in and out as you see fit for your data.
# under_model = MLPClassifier(hidden_layer_sizes=(10, 10, 10),
#                             max_iter=1000)
# # under_model = LinearRegression(fit_intercept=True,
# #                                copy_X=True, n_jobs=2)
# myModel = make_pipeline(StandardScaler(with_mean=False),
#                       under_model)
# model = KNeighborsClassifier(n_neighbors=2)

# print(X_train)
# print(X_train.shape)
# print(type(X_train))

# Fit/Train your model and predict
# Note these two lines are the same for all the models
# due to the common API/interface of sklearn
# model.fit(X_train.values.reshape(-1, 1), y_train)
# y_pred = model.predict(X_test.values.reshape(-1, 1))
# # print(y_pred)
# # print(y_pred.shape)
# # print(type(y_pred))
#
# # Make a new dataframe to house and plot predictions
# df_pred = pd.DataFrame()
# df_pred['Predicted Temperature'] = y_pred
# df_pred['Observed Temperature Validation Set'] = y_test
# df_pred['X_test'] = X_test
# df_pred = df_pred.dropna()  # get rid of NaNs
#
# # Convert back to original date strings from ordinal for graphing
# df_pred['DATE'] = df_pred['X_test'].astype(int)\
#     .map(datetime.datetime.fromordinal)
# print(df_pred.head(3))
# # Plot Predicted y (Observed Temperature) vs Time
# axes = df_pred.plot('DATE', 'Predicted Temperature', color='orange')
# plt.tight_layout()
# plt.show()
#
# # fig() / create_figure()
# fig = axes.get_figure()
# img = io.BytesIO()
# img.seek(0)
# fig.savefig(img, format="png")
# return send_file(img, mimetype="image/png")  # in flask
