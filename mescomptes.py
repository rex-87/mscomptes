import os
import pandas as pd
import datetime
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import datetime

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

def GetSavingsDelta(deb, cre):
    return cre - deb

df['Savings Delta'] = GetSavingsDelta(df['Debit Amount'].fillna(0), df['Credit Amount'].fillna(0))
df['Savings'] = np.cumsum(df['Savings Delta'])
df['Savings n=30'] = df['Savings'].rolling(30).mean()
df['Savings n=90'] = df['Savings'].rolling(90).mean()
df['Savings n=360'] = df['Savings'].rolling(360).mean()
# print(df)
# import pdb; pdb.set_trace()

plt.plot_date(dateconv(df['Timestamp']), df['Savings'], 'b.', markersize = 1,)
plt.plot_date(dateconv(df['Timestamp']), df['Savings n=30'], 'r-')
plt.plot_date(dateconv(df['Timestamp']), df['Savings n=90'], 'g-')
plt.plot_date(dateconv(df['Timestamp']), df['Savings n=360'], 'y-')
plt.gca().xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(12))
plt.gca().yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(5))
plt.grid()
plt.grid(which = 'minor', linestyle = '--', alpha = 0.5)
plt.show()