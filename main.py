#!/usr/bin/python3

import datetime as dt
import dateutil.relativedelta
import os
import requests
import timeutils
import csv

CACHE_DIR = "cache"
CACHE_FILE_TEMPLATE  = "cache_{}_{}_{}.data"
NFF_URL_TIMEFORMAT   = "%d.%m.%Y"
NFF_INPUT_TIMEFORMAT = "%d.%m.%Y %H:%M"
OUTSIDE_DATA_URL     = "http://umweltdaten.nuernberg.de/csv/wetterdaten/messstation-nuernberg-flugfeld/archiv/csv-export/SUN/nuernberg-flugfeld/{dtype}/individuell/{fromDate}/{toDate}/export.csv"

headers = [ "Datum/Zeit", "Temperatur [°C]", "rel. Luftfeuchte [%]", "Luftdruck [mbar]", "Windgeschwindigkeit [m/s]", "Windrichtung N=0, O=90, S=180, W=270", "Niederschlag [mm = L/m2]"]
dtypes  = [ "lufttemperatur-aussen", "luftfeuchte", "luftdruck", "windgeschwindigkeit", "windrichtung", "niederschlagsmenge" ]

def downloadFlugfeldData(fromTime, toTime, dtype):

    # prepare strings #
    cacheDir    = CACHE_DIR
    fromTimeStr = fromTime.strftime(NFF_URL_TIMEFORMAT)
    toTimeStr   = toTime.strftime(NFF_URL_TIMEFORMAT)
    cacheFile   = CACHE_FILE_TEMPLATE.format(dtype, fromTimeStr, toTimeStr)
    fullpath    = os.path.join(cacheDir, cacheFile)

    # check for cache file
    content = None
    if not os.path.isfile(fullpath):
        url = OUTSIDE_DATA_URL.format(dtype=dtype, fromDate=fromTimeStr, toDate=toTimeStr)
        r = requests.get(url)
        content = r.content.decode('utf-8', "ignore") # ignore bad bytes

        # cache data
        if not os.path.isdir(cacheDir):
            os.mkdir(cacheDir)
        with open(fullpath, 'w') as f:
            f.write(content)
    else:
        with open(fullpath) as f:
            content = f.read()

    return content

def checkLastMonths(backwardsMonths=6):
   
    fullContentDict = dict()

    today = dt.datetime.today() 
    monthsToCheck = [ today.month - x for x in range(0, backwardsMonths)  ]
    monthsToCheckFixed = list(map(lambda x: x if x > 0 else x + 12, monthsToCheck))

    for monthNumber in monthsToCheckFixed:
        
        year = today.year
        if monthNumber > today.month:
            year = today.year - 1
        start = dt.datetime(year=year, month=monthNumber, day=1)
        end = start + dateutil.relativedelta.relativedelta(months=+1, seconds=-1)

        # check special cases #
        if end > today:
            end = today - dt.timedelta(days=1)
            if start > end:
                return ""

        for dtype in dtypes:
            content = downloadFlugfeldData(start, end, dtype)
            dataList = parse(content, dtype)
            for d in dataList:
                if d.time in fullContentDict:
                    fullContentDict[d.time] += [d]
                else:
                    fullContentDict.update({ d.time : [d] })

    return fullContentDict

def parse(content, dtype):
    skipBecauseFirstLine = True
    dataList = []
    for l in content.split("\n"):
        if not ";" in l:
            continue
        elif not l.strip():
            continue
        elif skipBecauseFirstLine:
            skipBecauseFirstLine = False
            continue
        try:
            timeStr, value = l.split(";")
            timestamp = dt.datetime.strptime(timeStr, NFF_INPUT_TIMEFORMAT)
            cleanFloat = value.replace(",",".")

            # - means the value is missing in the data set (happens sometimes) #
            if cleanFloat.strip() == "-" or cleanFloat.strip() == "+":
                continue

            dataList += [Data(dtype, float(cleanFloat), timestamp)]

        except ValueError as e:
            print("Warning: {}".format(e))

    return dataList

class Data:
    def __init__(self, dtype, value, time):
        self.dtype = dtype
        self.value = value
        self.time  = time

    def __str__(self):
        return "Data: {} {} {}".format(self.dtype, self.time, self.value)

if __name__ == "__main__":
    dictForCSV = checkLastMonths()

    with open('test.csv', 'w', newline='') as file:

        fieldnames = ["time"] + dtypes
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for key in dictForCSV.keys():
            rowdict = { "time" : key }
            for data in dictForCSV[key]:
                rowdict.update({ data.dtype : data.value })
            writer.writerow(rowdict) 

