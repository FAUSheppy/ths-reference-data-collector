#!/usr/bin/python3

import datetime as dt
import dateutil.relativedelta
import os
import requests
import csv
import pyexcel.cookbook
import pyexcel
import glob
import calendar


CSV_DIR = "csvfiles"
CACHE_DIR = "cache"
CACHE_FILE_TEMPLATE  = "cache_{}_{}_{}.data"
NFF_URL_TIMEFORMAT   = "%d.%m.%Y"
NFF_INPUT_TIMEFORMAT = "%d.%m.%Y %H:%M"
OUTSIDE_DATA_URL     = "http://umweltdaten.nuernberg.de/csv/wetterdaten/messstation-nuernberg-flugfeld/archiv/csv-export/SUN/nuernberg-flugfeld/{dtype}/individuell/{fromDate}/{toDate}/export.csv"

headerMappings = { 
            "time"                  : "Datum/Zeit", 
            "lufttemperatur-aussen" : "Temperatur [°C]",
            "kelvin"                : "Temperatur [K]" ,
            "luftfeuchte"           : "rel. Luftfeuchte [%]",
            "luftdruck"             : "Luftdruck [mbar]",
            "windgeschwindigkeit"   : "Windgeschwindigkeit [m/s]",
            "windrichtung"          : "Windrichtung N=0, O=90, S=180, W=270",
            "niederschlagsmenge"    : "Niederschlag [mm = L/m2]" }

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
   

    today = dt.datetime.today() 
    monthsToCheck = [ today.month - x for x in range(0, backwardsMonths)  ]
    monthsToCheckFixed = list(map(lambda x: x if x > 0 else x + 12, monthsToCheck))

    for monthNumber in monthsToCheckFixed:
        
        fullContentDict = dict()
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

        # parse and dump
        csvOut = os.path.join(CSV_DIR, 'Wetterdaten-{}-{}.csv'.format(
                                            calendar.month_name[monthNumber], year))
        with open(csvOut, 'w', newline='', encoding="utf-8") as file:

            fieldnames = list(headerMappings.values())
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()

            for key in fullContentDict.keys():
                rowdict = { headerMappings["time"] : key }
                for data in fullContentDict[key]:
                    rowdict.update({ headerMappings[data.dtype] : data.value })

                    # calc kelvin if temp #
                    if data.dtype == "lufttemperatur-aussen":
                        rowdict.update({ headerMappings["kelvin"] : data.value + 273 })
                
                writer.writerow(rowdict) 

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
    checkLastMonths()
    
    globPattern = "{}/*.csv".format(CSV_DIR)
    sheets = {}
    for f in glob.glob(globPattern):
        sheet = pyexcel.get_sheet(file_name=f, delimiter=";")
        sheets.update({ os.path.basename(f) : sheet })
    
    book = pyexcel.get_book(bookdict=sheets)
    book.save_as("Wetterdaten.xlsx")
