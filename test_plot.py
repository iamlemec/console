import numpy as np
import pandas as pd
from altair import Chart, load_dataset
from iconsole import IConsole
from time import sleep

# generate data
N = 4*366;

df1 = pd.DataFrame({
    'stock': np.exp(0.02*np.cumsum(np.random.randn(N))),
    'time': pd.date_range(start='2014-01-01',periods=N)
})

df2 = pd.DataFrame({
    'signal': np.sin(np.linspace(0.0,10.0,N)),
    'period': np.linspace(0.0,10.0,N)
})

# generate chart specs
ch1 = Chart(df1).mark_line().encode(x='time',y='stock')
ch2 = Chart(df2).mark_line().encode(x='period',y='signal')

# start server and create figures
ic = IConsole()
sleep(1)
fig1 = ic.create_plot().title('Random Walk').altair(ch1)
fig2 = ic.create_plot().title('Sine Wave').altair(ch2)

# hold
input()
