import requests
import json
import sys
import time
import datetime
import argparse
from currency_converter import CurrencyConverter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import re

CRED    = '\33[31m'
CGREEN  = '\33[32m'
ENDC    = '\033[0m'

SEC_IN_MIN  = 60
DEFAULT_SLEEP = (5 * SEC_IN_MIN) # 5 minutes

class Flight_Reader:
    def __init__(self, method : str):
        # ryanair-api or web
        # ryanair-api is fast and easy to use, but it doesn't provide all flights
        # direct web access should collect all data, but is very slow (5-10 sec per single flight)
        self._method = method

    def get_from_ryanair_api(self, departure : str, destination : str, date : str):
        url = "https://services-api.ryanair.com/farfnd/3/oneWayFares?&departureAirportIataCode={dep}&language=en&limit=100&market=en-gb&offset=0&outboundDepartureDateFrom={date}&outboundDepartureDateTo={date}&priceValueTo=150"
        url = url.format(dep = departure, date = date)

        try:
            r = requests.get(url)
        except requests.exceptions.RequestException as e:
            return False

        if not r.ok:
            return False

        flights = json.loads(r.content)

        for fare in flights['fares']:
            f_dep = fare['outbound']['departureAirport']['iataCode']
            f_dest = fare['outbound']['arrivalAirport']['iataCode']
            f_price = fare['outbound']['price']['value']
            f_curr = fare['outbound']['price']['currencyCode']

            if f_dep == departure and f_dest == destination:
                return [str(f_price), f_curr]
        return False

    def get_from_web(self, departure : str, destination : str, date : str):
        url = "https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut={to_date}&dateIn=&isConnectedFlight=false&discount=0&isReturn=false&promoCode=&originIata={ffrom}&destinationIata={fto}&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate={to_date}&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata={ffrom}&tpDestinationIata={fto}"
        url = url.format(ffrom = departure, fto = destination, to_date = date)
        print(url)

        # return flights:
        #url = "https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut={to_date}&dateIn={from_date}&isConnectedFlight=false&isReturn=true&discount=1&promoCode=&originIata={ffrom}&destinationIata={fto}&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate={to_date}&tpEndDate={from_date}&tpDiscount=0&tpPromoCode=&tpOriginIata={ffrom}&tpDestinationIata={fto}"
        #url = url.format(ffrom = args.dep, fto = args.dest, to_date = f_to_date_str, from_date = f_from_date_str)

        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)
        driver.set_page_load_timeout(5)
        try:
            # Page content is filled dynamically by js and randomly price was not available yet while reading.
            # Workaround is to wait for element that does not exist to give extra time before reading.
            driver.get(url)
            element_present = EC.presence_of_element_located((By.ID, 'xxx'))
            WebDriverWait(driver, 5).until(element_present)
        except TimeoutException:
            pass

        # Price is in zł(value) format: find such words
        # This needs to be adapted for other currencies
        result = re.findall(r'[z][ł][(1-9)]\S*', driver.page_source)
        curr = "PLN"
        skip = 2

        if len(result) < 1:
            result = re.findall(r'[€][(1-9)]\S*', driver.page_source)
            skip = 1
            curr = "EUR"

        driver.quit()

        if len(result) < 1:
            return False

        return [result[-1][skip:], curr]

    def read(self, departure : str, destination : str, date : str):
        if self._method == "ryanair-api":
            return self.get_from_ryanair_api(departure, destination, date)
        elif self._method == "web":
            return self.get_from_web(departure, destination, date)
        else:
            return False

class Fly_Info:
    def __init__(self, departure : str, destination : str, date, method : str):
        self._timestamp = ""
        self._date = date
        self._dep = departure
        self._dest = destination
        self._price = 0
        self._curr = ""
        self._method = method

    def read(self):
        now = datetime.datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")

        flight_reader = Flight_Reader(self._method)

        result = flight_reader.read(self._dep, self._dest, self._date)

        if result == False:
            return result

        self._timestamp = dt_string
        self._price = float(result[0])
        self._curr = result[1]
        return True

    def is_set(self):
        return True if self._timestamp != "" else False

class Travel_Info:
    def __init__(self, departure : str, destination : str, to_date : str, from_date: str, method : str):
        self._departure = departure
        self._destination = destination
        self._to_date = to_date
        self._from_date = from_date
        self._to = None
        self._from = None
        self._method = method

    def read(self):
        to_flight = Fly_Info(self._departure, self._destination, self._to_date, self._method)
        from_flight = Fly_Info(self._destination, self._departure, self._from_date, self._method)

        if(to_flight.read() == False or from_flight.read() == False):
            print(CRED + "Flights not found or connection error!" + ENDC)
            return False

        self._to = to_flight
        self._from = from_flight

        return True

    def txt(self):
        c = CurrencyConverter()
        to_price_pln = c.convert(self._to._price, self._to._curr, "PLN")
        from_price_pln = c.convert(self._from._price, self._from._curr, "PLN")
        total_pln = round(to_price_pln + from_price_pln, 2)

        txt =  "{timestamp}:  [{to_date} {to} ({to_price} {to_cur})] <--> [{from_date} {ffrom} ({from_price} {from_cur})] TOTAL PRICE: {total} PLN"
        txt = txt.format(timestamp = self._to._timestamp,
                    to_date = self._to._date, to = self._to._dep, to_price = self._to._price, to_cur = self._to._curr,
                    from_date = self._from._date, ffrom = self._from._dep, from_price = self._from._price, from_cur = self._from._curr,
                    total = total_pln)

        return txt

    def push(self, url : str):
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException as e:
            print(e.response)

            return False

        if not r.ok:
            return False

        print(r.content)
        return json.loads(r.content)

def get_flights(departure, day):

    url = "https://services-api.ryanair.com/farfnd/3/oneWayFares?&departureAirportIataCode={dep}&language=en&limit=100&market=en-gb&offset=0&outboundDepartureDateFrom={date}&outboundDepartureDateTo={date}&priceValueTo=150"
    url = url.format(dep = departure, date = day)

    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        return False

    if not r.ok:
        return False

    flights = json.loads(r.content)

    return flights

def monitor_flights(departure, arrivals, date, delay):
    prices = {}

    while(True):
        flights = get_flights(departure, date)

        if flights == False:
            time.sleep(delay)
            continue
        txt = ""

        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        print(dt_string, end=" ")

        for fare in flights['fares']:
            f_from = fare['outbound']['departureAirport']['iataCode']
            f_to = fare['outbound']['arrivalAirport']['iataCode']
            f_price = fare['outbound']['price']['value']
            f_cur = fare['outbound']['price']['currencyCode']

            if(f_to in arrivals):
                if not f_to in prices:
                    prices[f_to] = []
                prices[f_to].append(f_price)

                if(len(prices[f_to]) > 1 and prices[f_to][-1] != prices[f_to][-2]):
                    print('\a', end = "")
                    if(prices[f_to][-1] > prices[f_to][-2]):
                        txt = txt + CRED
                    else:
                        txt = txt + CGREEN

                txt = txt + "{ffrom} -> {fto} : {fprice:.2f} {fcur} " + ENDC + "; "
                txt = txt.format(ffrom = f_from, fto = f_to, fprice = f_price, fcur = f_cur)

        print(txt)
        time.sleep(delay)


def monitor_two_way(departure : str, destination : str, to_date : str, from_date : str,
                    method : str, next : int, delay : int):
    while(True):
        f_to = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
        f_from = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
        for i in range(0, next + 1):
            f_to_date_str = f_to.strftime("%Y-%m-%d")
            f_from_date_str = f_from.strftime("%Y-%m-%d")

            travel_info  = Travel_Info(departure, destination, f_to_date_str, f_from_date_str, method)
            if travel_info.read() == True:
                print(travel_info.txt())
                to_price_json = '{\"prices\": [\"' + str(travel_info._to._price) + '\", \"' + travel_info._to._curr + '\", \"' + travel_info._to._timestamp + '\"]}'
                from_price_json = '{\"prices\": [\"' + str(travel_info._from._price) + '\", \"' + travel_info._from._curr + '\", \"' + travel_info._from._timestamp + '\"]}'

                url = 'http://www.flyaway.cal24.pl/insert.php?to_port={to_port}&to_date={to_date}&to_price={to_price}&from_port={from_port}&from_date={from_date}&from_price={from_price}'
                url = url.format(to_port = travel_info._to._dep, to_date = travel_info._to_date, to_price = to_price_json,
                                 from_port = travel_info._from._dep, from_date = travel_info._from_date, from_price = from_price_json)

                print(url)
                status = travel_info.push(url)
                if not status == False:
                     print(status['status'])

            f_to = f_to + datetime.timedelta(days = 7)
            f_from = f_from + datetime.timedelta(days = 7)
        if delay == 0:
            return

        time.sleep(delay)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dep', type = str, required = True, help = "Departure airport code (please check codes on ryanair.com, e.g: BVA - Paris)")
    parser.add_argument('--dest', type = str, required = True, help = "Destination airport codes. Coma separated list. (please check codes on ryanair.com, e.g: GDN,WMI,KRK,POZ)")
    parser.add_argument('--day', type = str, required = True, help = "Day to search for flights in format YYYY-MM-DD, e.g: 2023-06-21")
    parser.add_argument('--rday', type = str, required = True, help = "Return day to search for flights in format YYYY-MM-DD, e.g: 2023-06-21")
    parser.add_argument('--mode', type = int, required = True, help = "1 - one way mode, 2 - return mode")
    parser.add_argument('--sleep', type = int, required = False, default = 0, help = "Delay between reads in minutes (min 1 minute, default 5 minutes)")
    parser.add_argument('--method', type = str, required = True, help = "api or web: api is simple and fast, but not all data is provided by ryanair; direct read from web should collect all data, but it take longer (5-10 sec per single flight) and requires selenium and chrome.")
    parser.add_argument('--next', type = int, required = False, default = 0, help = "Check also in successive next weeks")

    args = parser.parse_args()

    if args.sleep >= 1:
        delay = args.sleep * SEC_IN_MIN
    else:
        delay = 0

    if args.method != "api" and args.method != "web":
        print("Invalid mode, please see help for details.")
        return

    arrivals = args.dest.split(',')

    if args.mode == 1 :
        monitor_flights(args.dep, arrivals, args.day, delay)
    elif args.mode == 2:
        monitor_two_way(args.dep, args.dest, args.day, args.rday, args.method, args.next, delay)

if __name__ == "__main__":
    main()