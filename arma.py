# ARMA.py 
# June 2019

# Multifunctional script to train and predict
# using an ARMA model.
# Parameters are read from yaml file.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml
import sys
import os
#import matplotlib.dates as mdates
from pandas import DataFrame
#from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.stattools import adfuller
from pmdarima.arima import auto_arima
plt.style.use('grayscale')

# Load YAML file from environment
YAML_file = open(os.environ['YAML'])
try:
    config = yaml.safe_load(YAML_file)
except yaml.YAMLError as exc:
    print(exc)

# Optional stationarity evaluation
# using Augmented Dickey-Fuller 
# unit root tests.
def stationarity_report(df):
    
    # Raw data
    print(">> Raw data stationary:")
    dftest = adfuller(df.atLeastMean, autolag='AIC')
    print("Test statistic = {:.3f}".format(dftest[0]))
    print("P-value = {:.3f}".format(dftest[1]))
    print("Critical values :")
    
    for k, v in dftest[4].items():
        print("\t{}: {} - The data is {} stationary with {}% confidence.".format(k, v, "not" if v<dftest[0] else "", 100-int(k[:-1])))
    print()
    
    # De-trended data
    print(">> De-trended data stationary:")
    dftest = adfuller(df.z_data.dropna(), autolag='AIC')
    print("Test statistic = {:.3f}".format(dftest[0]))
    print("P-value = {:.3f}".format(dftest[1]))
    print("Critical values :")
    
    for k, v in dftest[4].items():
        print("\t{}: {} - The data is {} stationary with {}% confidence.".format(k, v, "not" if v<dftest[0] else "", 100-int(k[:-1])))
    print()

# Get lowest AIC ARMA model using grid 
# search hyperparameter selection.
# Paramter limits chosen from YAML file.
def get_model(data):
    model = auto_arima(data, start_p=0, start_q=0,
                           max_p=config['arma']['train_max_p'], max_q=config['arma']['train_max_q'],
                           seasonal=False,
                           trace=True,
                           error_action='ignore',  
                           suppress_warnings=True,
                           stepwise=False)
    
    return model

def train():
    
    print(">> Loading data . . .")

    # Raw Data
    data = pd.read_csv(config['arma']['data'], index_col=0, usecols=['date', 'atLeastMean'], parse_dates=['date'])
    
    # De-trend data using z-score differencing
    # over a 7 day window
    data['z_data'] = (data['atLeastMean'] - data.atLeastMean.rolling(window=7).mean()) / data.atLeastMean.rolling(window=7).std()
    
    # Perform optional report
    if config['arma']['stationarity_report']:
        print(">> Stationarity report . . .")
        stationarity_report(data)
    
    # Grab number of days and use that
    # to determine and build train
    # and test sets 
    days = config['arma']['num_pred_days']
    X = 0 - days
    train, test = data.z_data.dropna()[:X], data.z_data.dropna()[X:]

    # Calculate threshold
    std = train.std(axis=0, skipna=True)
    threshold = std / (config['arma']['threshold_denom'])
    
    # Train ARMA model and report metrics
    print(">> Training model . . .")
    model = get_model(train.values)
    print(">> ARMA model AIC: [{}]".format(model.aic()))
    preds = model.predict(test.shape[0])
    print(">> RMSE: [%.3f]" % np.sqrt(mean_squared_error(test, preds)))
    
    # Plot the data
    # Save off as desired
    fig, ax = plt.subplots(figsize=(14, 8))
    obs = pd.concat([train, test])
    ax.plot(train, color='black', label='train')
    ax.plot(test, color='black', ls='--', label='test')
    ax.errorbar(obs.index[train.shape[0]:], preds, yerr=threshold, color='black', marker='o', capsize=5, ecolor='black', alpha=0.5, label='predictions')
    plt.title("Train {} days, Predict {} days".format(train.shape[0], test.shape[0]))
    plt.xlabel("Date YYYY-MM-DD")
    plt.ylabel("Deflated Coeffecient Value")
    plt.xticks(rotation='45')
    plt.legend()
    plt.savefig("{}.png".format(config['arma']['plot']), format='png', bbox_inches='tight', dpi=300)

def main():

    print("ARMA Time")
    
    flag = sys.argv[1]

    if flag == 't':
        train()
    elif flag == 'p':
        predict()
    else:
        print("Usage: python3 [script] [mode]")

if __name__ == "__main__":
    main()
