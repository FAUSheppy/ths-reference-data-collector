## Reference Data Collector

This tool can be used to create well-formated excel-spreadsheets from the data provided by the weather station of [Nürnberg Flugfeld](http://umweltdaten.nuernberg.de/wetterdaten/messstation-nuernberg-flugfeld.html) or most other official weather stations in Germany.

It automatically downloads and combines the data of the last 6 months and outputs a single Excel-File with multiple sub-tables.

![Spreadsheet Example](https://images.potaris.de/media/weather_github_example_pic.PNG)

## Requirements

    openpyxl>3.0.3
    pyexcel>0.6.7
    pyexcel-xls>0.7.0
    pyexcel-xlsx>0.6.0

## Usage

    usage: main.py [-h] [--target-file TARGET_FILE]
