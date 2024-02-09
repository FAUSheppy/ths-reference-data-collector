import glob
import datetime
import os
import tkinter
import tkinter.messagebox
from plyer import notification

SKIP_LINES = 13
IGNORE_MISSING = False

DTYPES_MISSING_NOTIFIED = []

def send_warning_ignore(dtype):

    if dtype in DTYPES_MISSING_NOTIFIED:
        return
    else:
        DTYPES_MISSING_NOTIFIED.append(dtype)

    notification.notify(
        title='Klimadaten EXCEL',
        message='Datei fehlt für: {}'.format(dtype),
    )

def cache_content(from_time, to_time, data, dtype):

    return_string = ""

    skip_count = 0

    for i in range(0, SKIP_LINES):
        return_string += "\n"

    for d in data:

        date, primary, secondary = d

        # skip outside timeframe #
        if date < from_time or date > to_time:
            continue

        if dtype in ["lufttemperatur-aussen", "windgeschwindigkeit", "niederschlagsmenge"]:
            content_number = primary
        elif dtype in ["luftfeuchte", "windrichtung"]:
            content_number = secondary
        elif dtype == "luftdruck":
            content_number = -1
        else:
            raise ValueError("Bad dtype: {}".format(dtype))

        date_cache_format = date.strftime("%d.%m.%Y %H:%M")
        content_str = "{:1f}".format(content_number).replace(".",",")
        return_string += "{};{}\n".format(date_cache_format, content_str)

    return return_string

def generate(master_dir, from_time, to_time, cache_file, dtype):

    global IGNORE_MISSING

    if dtype == "lufttemperatur-aussen" or dtype == "luftfeuchte":
        base_name = "/produkt_tu_stunde*.txt"
    elif dtype == "windgeschwindigkeit" or dtype == "windrichtung":
        base_name = "/produkt_ff_stunde*.txt"
    elif dtype == "niederschlagsmenge":
        base_name = "/produkt_rr_stunde*.txt"
    elif dtype == "luftdruck":
        base_name = "/produkt_tu_stunde*.txt" # <- placeholder cause missing
    else:
        raise ValueError("Unsupported D-Type: {}".format(dtype))

    timeframes = []

    if not os.path.isdir(master_dir):
        os.mkdir(master_dir)

    # read files
    files = glob.glob(master_dir + base_name)
    if not files:
        if IGNORE_MISSING:
            send_warning_ignore(dtype)
            return ""

        description = "Keine DWD_Datei für {} gefunden!".format(dtype)
        description += "\nAlle fehlenden Dateien ignorieren und weiter?  ('Nein' bricht den Durchlauf ab)"
        root = tkinter.Tk()
        response = tkinter.messagebox.askyesno("Achtung", description)
        root.withdraw()
        if response:
            send_warning_ignore(dtype)
            IGNORE_MISSING=True
            return ""

    
    last_date = None
    for fname in files:

        start = None
        end = None
        data = []

        # read file
        with open(fname) as f:
            first_line = True

            # iterate through csv #
            for line in f:

                # skip header
                if first_line:
                    first_line = False
                    continue

                # read the line #
                # temp & feutche => fu
                # wind & direction => ff
                # niederschlag & nichts => rr
                if dtype == "niederschlagsmenge":
                    station_id, fulldate, dunno, primary, secondary, na2, na3 = line.split(";")
                else:
                    station_id, fulldate, dunno, primary, secondary, na2 = line.split(";")

                # parse date #
                date = datetime.datetime.strptime(fulldate, "%Y%m%d%H")
                last_date = date

                # append data #
                data.append((date, float(primary), float(secondary)))

                # set start and end #
                if not start and date:
                    start = date
                elif date:
                    end = date

        # save values #
        timeframes.append((start, end, data))
        print(dtype, start, end)
        print(dtype, from_time, to_time)

    # find a fitting frame #
    to_time = last_date - datetime.timedelta(hours=12)
    for start, end, data in timeframes:
        if from_time >= start and to_time <= end:
            return cache_content(from_time, to_time, data, dtype)

    if dtype.startswith("wind"):
        return ""
    raise ValueError("Keine Datei mit passenden Daten gefunden. Bitte Readme lesen")
