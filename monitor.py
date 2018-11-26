#!/usr/bin/env python
#Goes here: /usr/lib/cgi-bin/
#https://github.com/Pyplate/rpi_temp_logger
#http://raspberrywebserver.com/cgiscripting/rpi-temperature-logger/building-an-sqlite-temperature-logger.html

import sqlite3

import os
import time
import glob

# global variables
speriod=(15*60)-1
dbname='/var/www/templog.db'



# store the temperature in the database
def log_temperature(deviceIdentifier, temp):

    conn=sqlite3.connect(dbname)
    curs=conn.cursor()

    dev = deviceIdentifier[deviceIdentifier.rfind('/')+1:]
    
    sql = "INSERT INTO temps (timestamp, temp, deviceIdentifier) VALUES (datetime('now'), '{0}', '{1}')".format(temp, dev)
    
    curs.execute(sql)

    # commit the changes
    conn.commit()

    conn.close()


# display the contents of the database
def display_data():

    conn=sqlite3.connect(dbname)
    curs=conn.cursor()

    for row in curs.execute("SELECT * FROM temps"):
        print str(row[0])+"	"+str(row[1])

    conn.close()



# get temerature
# returns None on error, or the temperature as a float
def get_temp(devicefile):

    try:
        fileobj = open(devicefile,'r')
        lines = fileobj.readlines()
        fileobj.close()
    except:
        return None

    # get the status from the end of line 1 
    status = lines[0][-4:-1]

    # is the status is ok, get the temperature from line 2
    if status=="YES":
        print status
        tempstr= lines[1][-6:-1]
        
        #CS 20151122 - Handle temp being less than 6 digits
        equalIndex = tempstr.find('=')
        
        if equalIndex > -1:
            tempstr = tempstr[equalIndex+1:]
        
        tempvalue=float(tempstr)/1000
        print tempvalue
        return tempvalue
    else:
        print "There was an error."
        return None



# main function
# This is where the program starts 
def main():

    # enable kernel modules
    os.system('sudo modprobe w1-gpio')
    os.system('sudo modprobe w1-therm')

    # search for a device file that starts with 28
    devicelist = glob.glob('/sys/bus/w1/devices/28*')
    if devicelist=='':
        return None
		
	#CS 20151122 - Log all devices
    for dev in devicelist:
    
        w1devicefile = dev + '/w1_slave'

        # get the temperature from the device file
        temperature = get_temp(w1devicefile)
        if temperature != None:
            print "dev/temperature = {0} / {1}".format(dev, str(temperature))
        else:
            # Sometimes reads fail on the first attempt
            # so we need to retry
            temperature = get_temp(w1devicefile)
            print "SECOND ATTEMPT: dev/temperature = {0} / {1}".format(dev, str(temperature))

            # Store the temperature in the database
        log_temperature(dev, temperature)



if __name__=="__main__":
    main()



