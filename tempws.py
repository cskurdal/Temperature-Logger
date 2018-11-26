#!/usr/bin/env python

#Goes here: /usr/lib/cgi-bin/

import sqlite3
import restlite
from restlite import tojson
import cgi
import cgitb

dbname = '/var/www/templog.db'
COLUMN_TIMESTAMP = 0
COLUMN_DATA = 1
COLUMN_DEVICE_IDENTIFIER = 2


# print the HTTP header
def printHTTPheader():
    print "Content-type: text/json\n\n"


# get data from the database
# if an interval is passed, 
# return a list of records from the database
def get_data(interval, uom = "F"):

    conn=sqlite3.connect(dbname)
    curs=conn.cursor()

    if uom and uom == "F":
        select = "timestamp, (temp * 9 / 5) + 32 AS temp, deviceIdentifier"
    else:
        select = "timestamp, temp, deviceIdentifier"
    
    
    curs.execute("SELECT {0} FROM temps WHERE timestamp>datetime('now','-{1} hours')\
            ORDER BY deviceIdentifier, timestamp".format(select, interval))


    rows=curs.fetchall()

    conn.close()

    return rows


def getCurrentTemp(interval = 2, uom = "F"):
    response = []

    rows = get_data(interval, uom)
    
    for row in rows:
        response.append((('deviceIdentifier', row[COLUMN_DEVICE_IDENTIFIER]), ('timestamp', row[COLUMN_TIMESTAMP]), ('temp', row[COLUMN_DATA])))

    return str(tojson(response))


# main function
# This is where the program starts 
def main():
    cgitb.enable()
    
    form=cgi.FieldStorage()
    
    
    #Set interval
    if "interval" in form:
        interval = form["interval"].value
        
    try:
        interval = int(interval)
    except:
        interval = 1
    
    uom = "F"
    
    if "uom" in form:
        if form["uom"].value == "C":
            uom = "C"
    
    # print the HTTP header
    printHTTPheader()
    
    print getCurrentTemp(interval, uom)
    
    return
    

if __name__=="__main__":
    main()



