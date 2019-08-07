import os
import pandas as pd
import datetime
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import datetime
import copy
from scipy import signal

# search for Lloyds csv files
CsvPathList = []
for root, dirs, files in os.walk(r".\raw\Lloyds"):
    for name in files:
        if ".csv" in name:
            CsvPathList.append(os.path.join(root, name))

# merge Lloyds csv files
MergedLloydsCsvPath = r'.\proc\Lloyds_merged.csv'
with open(MergedLloydsCsvPath, 'w') as fout:
    
    # copy csv files removing repeted lines
    UniqueLineList = []
    for CsvPath in CsvPathList:
        
        with open(CsvPath, 'r') as fin:
            fin_lines = fin.readlines()
        
        # for each input file line
        for fin_line in fin_lines:
            if fin_line in UniqueLineList:
                # line was already present in another file, ignore
                continue
            else:
                # This line is unique, save it ...
                UniqueLineList.append(fin_line) 
                # ... and copy it to the output file
                fout.write(fin_line)

# read merged lloyds csv
MergedLloydsDf = pd.read_csv(MergedLloydsCsvPath)

# append timestamp column
TimestampDf = pd.DataFrame(
    { 'Timestamp' : [ datetime.datetime.strptime(DateStr, "%d/%m/%Y").timestamp() for DateStr in MergedLloydsDf['Transaction Date']] },
)
MergedLloydsDf = MergedLloydsDf.join(TimestampDf)

# save processed lloyds csv
ProcLloydsCsvPath = r'.\proc\Lloyds_proc.csv'
MergedLloydsDf.to_csv(path_or_buf = ProcLloydsCsvPath)

dateconv = np.vectorize(datetime.datetime.fromtimestamp)
df = MergedLloydsDf[~MergedLloydsDf['Transaction Description'].str.contains('R THIBAULT')].sort_values(by = 'Timestamp')

tl = list(set(df[df.duplicated(subset='Timestamp', keep = False)]['Timestamp']))
new_entries_df = pd.DataFrame(columns = df.columns)
for t in tl:
    new_entry_ser = df[df['Timestamp'] == t][['Debit Amount', 'Credit Amount']].sum()
    new_entry_ser['Timestamp'] = t
    new_entries_df = new_entries_df.append(new_entry_ser, ignore_index = True)
    df = df[df['Timestamp'] != t]

df = df.append(new_entries_df)
df = df.sort_values(by = 'Timestamp').reset_index()

dfd = copy.copy(df['Timestamp'].diff()[1:])
dfd = copy.copy(dfd[dfd != 86400])

for i in dfd.index:
    new_entry_ser = copy.copy(df.loc[i])
    missing_days_count = int(dfd.loc[i]/86400 - 1)
    # print(i, missing_days_count)
    for j in range(missing_days_count):
        new_entry_ser = copy.copy(new_entry_ser)
        new_entry_ser['Debit Amount'] = 0
        new_entry_ser['Credit Amount'] = 0
        new_entry_ser['Timestamp'] = new_entry_ser['Timestamp'] - 86400
        df = df.append(new_entry_ser)

df = df.sort_values(by = 'Timestamp').reset_index()
# print(df['Timestamp'][0:10])
# print(df['Timestamp'].diff()[0:10])
# import pdb; pdb.set_trace()

def GetSavingsDelta(deb, cre):
    return cre - deb

df['Savings Delta'] = GetSavingsDelta(df['Debit Amount'].fillna(0), df['Credit Amount'].fillna(0))
df['Savings'] = np.cumsum(df['Savings Delta'])
d1m = 30;  df['Savings 1m'] = df['Savings'].rolling(d1m).mean()
d3m = 90;  df['Savings 3m'] = df['Savings'].rolling(d3m).mean()
d1y = 366; df['Savings 1y'] = df['Savings'].rolling(d1y).mean()
b, a = signal.butter(2, 0.004)
df['Savings Butterworth'] = signal.filtfilt(b, a, df['Savings'], padlen = 300)
# df['Savings Butterworth'] = signal.lfilter(b, a, df['Savings'])
# print(df)
# import pdb; pdb.set_trace()

plt.plot_date(dateconv(df['Timestamp']), df['Savings'], 'k.', markersize = 1,)
plt.plot_date(dateconv(df['Timestamp'][:-d1m//2]), df['Savings 1m'][d1m//2:], 'y-')
plt.plot_date(dateconv(df['Timestamp'][:-d3m//2]), df['Savings 3m'][d3m//2:], 'g-')
plt.plot_date(dateconv(df['Timestamp'][:-d1y//2]), df['Savings 1y'][d1y//2:], 'b-')
plt.plot_date(dateconv(df['Timestamp']), df['Savings Butterworth'], 'r-')
plt.gca().xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(12))
plt.gca().yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(5))
plt.grid()
plt.grid(which = 'minor', linestyle = '--', alpha = 0.5)
plt.show()

# plt.plot_date(dateconv(df['Timestamp']), df['Savings 1m'].diff(), 'r-')
# plt.plot_date(dateconv(df['Timestamp']), df['Savings 3m'].diff(), 'g-')
# plt.plot_date(dateconv(df['Timestamp']), df['Savings'].diff(), 'r-')
plt.plot_date(dateconv(df['Timestamp'][:-d1y//2]), df['Savings 1y'][d1y//2:].diff(), 'b-')
plt.plot_date(dateconv(df['Timestamp']), df['Savings Butterworth'].diff(), 'r-')
plt.gca().xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(12))
plt.gca().yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(5))
plt.grid()
plt.grid(which = 'minor', linestyle = '--', alpha = 0.5)
plt.show()