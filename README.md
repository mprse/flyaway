# Flyaway
Python script to search for cheep Ryan-air flights.

Script checks prices for the specified flights and prints flight details in the specified time intervals.
When the price changes, new prices are marked red if the price goes up and green if the price goes down.
Price change is also indicated by a beep signal.

## Quick start

Open console.

1. Install GIT

Windows

`winget install --id Git.Git -e --source winget`

Linux

`sudo apt install git-all`

2. Install python 3.xx

Windows
Install via windows store or [download](https://www.python.org/downloads/windows) and run installer.

Linux

`sudo apt install python3`

3. Clone this repository

`git clone https://github.com/mprse/flyaway.git`

`cd flyaway`


4. Install required python modules

`pip install requests`

`pip install termcolor`

`pip install colorama`

## Example usage

`python3 flyaway.py --dep BVA --arr GDN,WMI,KRK,POZ --day 2023-06-21 --sleep 2`

This will check flights from Paris (BVA) to Gdansk(GDN), Warsaw(WMI), Cracow(KRK) and Poznan(POZ) on 2023-06-21, every 2 minutes.

Note: please update the date to the valid one.

```
python3 flyaway.py -h
usage: flyaway.py [-h] --dep DEP --arr ARR --day DAY [--sleep SLEEP]

optional arguments:
  -h, --help     show this help message and exit
  --dep DEP      Departure airport code (please check codes on ryanair.com, e.g: BVA - Paris)
  --arr ARR      Arrival airport codes. Comma separated list. (please check codes on ryanair.com, e.g: GDN,WMI,KRK,POZ)
  --day DAY      Day to search for flights in format YYYY-MM-DD, e.g: 2023-06-21
  --sleep SLEEP  Delay between reads in minutes (min 1 minute, default 5 minutes)
```

![image](https://github.com/mprse/flyaway/assets/30721012/0f3f0df4-cf93-4ce4-88c0-568ec6540e68)
