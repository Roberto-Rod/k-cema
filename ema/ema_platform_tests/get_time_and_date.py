#!/usr/bin/env python3
import os


def run_test():
    print("")
    print("get_time_and_date")
    print("-----------------") 
    day = 0
    while (day < 1) or (day > 31):
        try:
            day = int(input("Enter day of the month (1 to 31): "))
        except:
            day = 0
            
    month = 0
    while (month < 1) or (month > 12):
        try:
            month = int(input("Enter month (1 to 12): "))
        except:
            month = 0
     
    year = 0
    while (year < 2020) or (year > 2100):
        try:
            year = int(input("Enter year (four-digits e.g. 2020): "))
        except:
            year = 0
     
    hour = -1
    while (hour < 0) or (hour > 23):
        try:
            hour = int(input("Enter hour (24-hour format, 0 to 23): "))
        except:
            hour = -1
            
    minute = -1
    while (minute < 0) or (minute > 59):
        try:
            minute = int(input("Enter minutes (0 to 59): "))
        except:
            minute = 0
    
    second = -1
    while (second < 0) or (second > 59):
        try:
            second = int(input("Enter seconds (0 to 59): "))
        except:
            second = 0
            
    os.system("/bin/date +%Y%m%d%T -s '{:04d}{:02d}{:02d} {:02d}:{:02d}:{:02d}';date".format(year, month, day, hour, minute, second))
    return True


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
