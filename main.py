#!/usr/bin/python3

import datetime as dt
import dateutil.relativedelta
import os

CACHE_DIR = "cache"
CACHE_FILE_TEMPLATE  = "cache_{}_{}_{}.data"
NFF_URL_TIMEFORMAT   = "%d.%m.%Y"
NFF_INPUT_TIMEFORMAT = "%d.%m.%Y %H:%M"
OUTSIDE_DATA_URL     = "http://umweltdaten.nuernberg.de/csv/wetterdaten/messstation-nuernberg-flugfeld/archiv/csv-export/SUN/nuernberg-flugfeld/{dtype}/individuell/{fromDate}/{toDate}/export.csv"

dtypes = [ "lufttemperatur-aussen", "luftfeuchte", "luftdruck" ]

def downloadFlugfeldData(fromTime, toTime, dtype):

    # prepare strings #
    cacheDir    = CACHE_DIR
    fromTimeStr = fromTime.strftime(NFF_URL_TIMEFORMAT)
    toTimeStr   = toTime.strftime(NFF_URL_TIMEFORMAT)
    cacheFile   = CACHE_FILE_TEMPLATE.format(dtype, fromTimeStr, toTimeStr)
    fullpath    = os.path.join(cacheDir, cacheFile)
    print(cacheFile)

    # check for cache file
    content = None
    if not os.path.isfile(fullpath):
        url = OUTSIDE_DATA_URL.format(dtype=dtype, fromDate=fromTimeStr, toDate=toTimeStr)
        print(url)
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

if __name__ == "__main__":
    checkLastMonths()
