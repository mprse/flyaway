import requests
import json
import sys
import time
from datetime import datetime
import argparse
from termcolor import colored
import colorama

SEC_IN_MIN  = 60
DEFAULT_SLEEP = (5 * SEC_IN_MIN) # 5 minutes

parser = argparse.ArgumentParser()
parser.add_argument('--dep', type = str, required = True, help = "Departure airport code (please check codes on ryanair.com, e.g: BVA - Paris)")
parser.add_argument('--arr', type = str, required = True, help = "Arrival airport codes. Comma separated list. (please check codes on ryanair.com, e.g: GDN,WMI,KRK,POZ)")
parser.add_argument('--day', type = str, required = True, help = "Day to search for flights in format YYYY-MM-DD, e.g: 2023-06-21")
parser.add_argument('--sleep', type = int, required = False, help = "Delay between reads in minutes (min 1 minute, default 5 minutes)")

args = parser.parse_args()

colorama.init()

if args.sleep == None:
    delay = DEFAULT_SLEEP
else:
    if args.sleep >= 1:
        delay = args.sleep * SEC_IN_MIN
    else:
        delay = DEFAULT_SLEEP

arrivals = args.arr.split(',')

url = "https://services-api.ryanair.com/farfnd/3/oneWayFares?&departureAirportIataCode={xdep}&language=en&limit=100&market=en-gb&offset=0&outboundDepartureDateFrom={xdate}&outboundDepartureDateTo={xdate}&priceValueTo=150"
url = url.format(xdep = args.dep, xdate = args.day)

prices = {}

while(True):
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(colored("Unable to download flights. Check internet connection!", "red"))
        time.sleep(delay)
        continue
    if r.ok:
        flights = json.loads(r.content)
        txt = ""

        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        print(dt_string, end=" ")

        for fare in flights['fares']:
            f_from = fare['outbound']['departureAirport']['iataCode']
            f_to = fare['outbound']['arrivalAirport']['iataCode']
            f_price = fare['outbound']['price']['value']
            f_cur = fare['outbound']['price']['currencyCode']

            txt_color = "white"

            if(f_to in arrivals):
                if not f_to in prices:
                    prices[f_to] = []
                prices[f_to].append(f_price)

                if(len(prices[f_to]) > 1 and prices[f_to][-1] != prices[f_to][-2]):
                    print('\a', end = "")
                    if(prices[f_to][-1] > prices[f_to][-2]):
                        txt_color = "red"
                    else:
                        txt_color = "green"

                txt = txt + "{ffrom} -> {fto} : {fprice:.2f} {fcur} "
                txt = txt.format(ffrom = f_from, fto = f_to, fprice = f_price, fcur = f_cur)
                txt = colored(txt, txt_color)
                txt = txt + '; '

        print(txt)
    else:
        print(colored("Unable to download flights. Check internet connection!", "red"))
    time.sleep(delay)
