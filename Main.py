import requests
import datetime
import time
import csv
import sys
import os

symbol = 'aapl'


def round_float(string):
    return round(float(string), 3)


def get_current_raw_data(API_URL, symbol, data):
    try:
        response = requests.get(API_URL, data)
        print(response.status_code)
        json = response.json()
    except requests.exceptions.RequestException as e:
        print("Error: {}".format(e))
        sys.exit(1)
    raw_recent_data = (json['Time Series (Daily)'])
    keys = (raw_recent_data.keys())
    print("Stock Ticker: " + symbol.upper())
    return raw_recent_data, keys


def extract_data(raw_recent_data, keys):
    recent_data = []
    line_count = 0
    for key in keys:
        if line_count != 0:
            recent_data.append(
                [key, round_float(raw_recent_data[key]['1. open']), round_float(raw_recent_data[key]['4. close'])])
        line_count += 1
    if not os.path.exists("./Historic_Data/" + str(symbol) + ".csv"):
        print("ERROR: Specified stock ticker historic data is unavailable")
    else:
        csv_file = open("./Historic_Data/" + str(symbol) + ".csv")
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        historic_data = []
        for row in csv_reader:
            if line_count != 0:
                historic_data.append([row[0], round_float(row[1]), round_float(row[4])])
            line_count += 1
        full_data = sorted(set(tuple(i) for i in (recent_data + historic_data)))
        return full_data


def get_year_span(data_list):
    oldest_year = min(int(data[0].split("-")[0]) for data in data_list)
    current_year = max(int(data[0].split("-")[0]) for data in data_list)
    year_span_size = int(current_year) - int(oldest_year) + 1
    year_span = []
    for i in range(year_span_size):
        year_span.append(int(oldest_year) + i)


def apply_month_range(data_list, month_range):
    filtered_data_list = []
    if not month_range:
        for data_point in data_list:
            filtered_data_list.append([data_point[0], (data_point[1]), (data_point[2])])
    else:
        for data_point in data_list:
            if data_point[0].split("-")[1] in month_range:
                filtered_data_list.append([data_point[0], (data_point[1]), (data_point[2])])
    return filtered_data_list


def max_delta(data_list):
    max_increase = [0, ""]
    max_decrease = [0, ""]
    for data_point in data_list:
        delta = 100 * (data_point[2] - data_point[1]) / data_point[1]
        if delta > max_increase[0]:
            max_increase = [delta, data_point[0]]
        if delta < max_decrease[0]:
            max_decrease = [delta, data_point[0]]
        max_increase[0] = round_float(max_increase[0])
        max_decrease[0] = round_float(max_decrease[0])
    print("Max Increase = " + str(max_increase[0]) + " On " + max_increase[1])
    print("Max Decrease = " + str(max_decrease[0]) + " On " + max_decrease[1])


def produce_final_data_list(API_URL, data):
    month_range = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    raw_recent_data, keys = get_current_raw_data(API_URL, symbol, data)
    data_list = apply_month_range(extract_data(raw_recent_data, keys), month_range)
    data_list.sort(key=lambda date: time.mktime(time.strptime(date[0], "%Y-%m-%d")))
    return data_list


def print_monthly_maximum_delta(data_list):
    month_range = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    month_name = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    count = 0
    for month in month_range:
        print("                 " + month_name[count])
        max_delta(apply_month_range(data_list, [month]))
        print("_____________________________________________")
        count += 1


def convert_price_to_delta(data_list):
    if len(data_list) == 2:
        return data_list
    for data_point in data_list:
        delta = 100 * (data_point[2] - data_point[1]) / data_point[1]
        data_point[1] = delta
        del(data_point[2])
    return data_list


def compare_past_dates(data_list, num_days):
    data_list = convert_price_to_delta(data_list)
    target_date_list = []
    for i in range(num_days):
        target_date = (datetime.date.today() + datetime.timedelta(days=i))
        day = str(target_date.day)
        if len(day) == 1:
            day = "0" + day
        month = str(target_date.month)
        if len(month) == 1:
            month = "0" + month
        target_date_list.append(month + "-" + day)
    target_delta_list = []
    same_date_list = []
    for target in target_date_list:
        for data in data_list:
            if data[0].split("-")[1] + "-" + (data[0]).split("-")[2] == target:
                same_date_list.append(data)
        target_delta_list.append(same_date_list)
        same_date_list = []

    for target_list in target_delta_list:
        pos_count = 0
        neg_count = 0
        date = ""
        for target in target_list:
            date = target[0].split("-")[1] + "-" + (target[0]).split("-")[2]
            if target[1] >= 0:
                pos_count += 1
            else:
                neg_count += 1
        pbty_up = 100 * pos_count / (pos_count + neg_count)
        pbty_down = 100 * neg_count / (pos_count + neg_count)
        print("On " + date + ": ")
        print("PBTY of increase = " + str(round_float(pbty_up)) + "%")
        print("PBTY of decrease = " + str(round_float(pbty_down)) + "%")
        print("Number of years = " + str(pos_count + neg_count))
        print("________________________________________________")

def main():
    API_URL = "https://www.alphavantage.co/query"
    data = {"function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",
            "apikey": "XXX"}
    dataList = produce_final_data_list(API_URL, data)
    # max_delta(dataList)
    # print_monthly_maximum_delta(dataList)
    # print(convert_price_to_delta(dataList))
    compare_past_dates(dataList, 30)
    # dataList = convert_price_to_delta(dataList)
    # for data in dataList:
    #    print(data[0].split("-")[1] + "-" + data[0].split("-")[2])


if __name__ == "__main__":
    main()
