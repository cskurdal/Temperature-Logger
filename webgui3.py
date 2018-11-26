#!/usr/bin/env python

#Goes here: /usr/lib/cgi-bin/
# Apache logs: /var/log/apache2/
#https://github.com/Pyplate/rpi_temp_logger
#http://raspberrywebserver.com/cgiscripting/rpi-temperature-logger/building-an-sqlite-temperature-logger.html

import sqlite3
import sys
import cgi
import cgitb


# global variables
speriod=(15*60)-1
dbname='/var/www/templog.db'
demo = False
useHighCharts = True


# print the HTTP header
def printHTTPheader():
    print "Content-type: text/html\n\n"



# print the HTML head section
# arguments are the page title and the table for the chart
def printHTMLHead(title, table):
    print "<head>"
    print "    <title>"
    print title
    print "    </title>"
    
    print_graph_script(table)

    print "</head>"


# get data from the database
# if an interval is passed, 
# return a list of records from the database
def get_data(interval, uom = "C"):

    conn=sqlite3.connect(dbname)
    curs=conn.cursor()

    if uom and uom == "F":
        select = "timestamp, (temp * 9 / 5) + 32 AS temp, deviceIdentifier"
    else:
        select = "timestamp, temp, deviceIdentifier"
    
    
    if interval == None:
        curs.execute("SELECT {0} FROM temps".format(select))
    else:
        if not demo:
            curs.execute("SELECT {0} FROM temps WHERE timestamp>datetime('now','-{1} hours')\
            ORDER BY deviceIdentifier, timestamp".format(select, interval))
        else:
            curs.execute("SELECT {0} FROM temps WHERE timestamp>datetime('2013-09-19 21:30:02','-{1} hours') AND timestamp<=datetime('2013-09-19 21:31:02')".format(select, interval))

    rows=curs.fetchall()

    conn.close()

    return rows

    
#CS 20151122 Returns the series string for highchart_code
def get_series_string(rows):
    #timestamp, temp, deviceIdentifier ordered by deviceIdentifier
    COLUMN_TIMESTAMP = 0
    COLUMN_DATA = 1
    COLUMN_DEVICE_IDENTIFIER = 2
    current_device = None
    device_count = 0
    string = ""
    new_device = False
    
    for row in rows:
        if not current_device or current_device != row[COLUMN_DEVICE_IDENTIFIER]:
            new_device = True
            current_device = row[COLUMN_DEVICE_IDENTIFIER]
            
        if new_device:
            new_device = False
            if device_count > 0: #close previous
                string += "]},"
                
            device_count = device_count + 1
            string += "{{name : '{0}', data : [".format(current_device)
        
        string += "['{0}', {1}], ".format(row[COLUMN_TIMESTAMP], row[COLUMN_DATA])
    
    if device_count > 0: #close last
        string += "]}"
    
    #print "\r\nseries string: {0}".format(string)
    
    return string

# convert rows from database into a javascript table
def create_table(rows):
    chart_table=""
    
    if useHighCharts:
        return get_series_string(rows)
        
        dates = ""
        temps = ""
        deviceIdentifier = ""
        
        for row in rows[:-1]:
            dates += "'{0}',".format(str(row[0]))
            temps += "{0},".format(str(row[1]))
            
        row = rows[-1]
        dates += "'{0}'".format(str(row[0]))
        temps += "{0}".format(str(row[1]))
        
        return dates, temps
    else:
        for row in rows[:-1]:
            rowstr="['{0}', {1}],\n".format(str(row[0]),str(row[1]))
            chart_table+=rowstr

        row=rows[-1]
        rowstr="['{0}', {1}]\n".format(str(row[0]),str(row[1]))
        chart_table+=rowstr

    return chart_table


# print the javascript to generate the chart
# pass the table generated from the database info
def print_graph_script(table):

    # google chart snippet
    chart_code="""
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
        var data = google.visualization.arrayToDataTable([
          ['Time', 'Temperature'],
%s
        ]);

        var options = {
          title: 'Temperature'
        };

        var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
        chart.draw(data, options);
      }
    </script>"""

    highchart_code = """
    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
    <script src="http://code.highcharts.com/highcharts.js"></script>
    <script src="http://code.highcharts.com/modules/exporting.js"></script>
    <script type="text/javascript">
    $(function () {
    
    $('#chart_div').highcharts({
        chart: {
            zoomType: 'x',
            type: 'spline'
        },
        title: {
            text: 'Temperature'
        },
        subtitle: {
            text: 'Source: Calebs Raspberry Pi'
        },
        xAxis: {
            type: 'datetime',
            dateTimeLabelFormats: { // don't display the dummy year
                month: '%e. %b',
                year: '%b'
            },
            title: {
                text: 'Date'
            }
        },
        yAxis: {
            title: {
                text: 'Temperature'
            }
        },
        tooltip: {
            headerFormat: '<b>{series.name}</b><br>',
            pointFormat: '{point.x:%e. %b}: {point.y:%s}'
        },
        plotOptions: {
            line: {
                dataLabels: {
                    enabled: true
                },
                enableMouseTracking: true
            }
        },
        series: [%s]
    });
});

/**
 * Dark theme for Highcharts JS
 * @author Torstein Honsi
 */

// Load the fonts
Highcharts.createElement('link', {
   href: '//fonts.googleapis.com/css?family=Unica+One',
   rel: 'stylesheet',
   type: 'text/css'
}, null, document.getElementsByTagName('head')[0]);

Highcharts.theme = {
   colors: ["#2b908f", "#90ee7e", "#f45b5b", "#7798BF", "#aaeeee", "#ff0066", "#eeaaee",
      "#55BF3B", "#DF5353", "#7798BF", "#aaeeee"],
   chart: {
      backgroundColor: {
         linearGradient: { x1: 0, y1: 0, x2: 1, y2: 1 },
         stops: [
            [0, '#2a2a2b'],
            [1, '#3e3e40']
         ]
      },
      style: {
         fontFamily: "'Unica One', sans-serif"
      },
      plotBorderColor: '#606063'
   },
   title: {
      style: {
         color: '#E0E0E3',
         textTransform: 'uppercase',
         fontSize: '20px'
      }
   },
   subtitle: {
      style: {
         color: '#E0E0E3',
         textTransform: 'uppercase'
      }
   },
   xAxis: {
      gridLineColor: '#707073',
      labels: {
         style: {
            color: '#E0E0E3'
         }
      },
      lineColor: '#707073',
      minorGridLineColor: '#505053',
      tickColor: '#707073',
      title: {
         style: {
            color: '#A0A0A3'

         }
      }
   },
   yAxis: {
      gridLineColor: '#707073',
      labels: {
         style: {
            color: '#E0E0E3'
         }
      },
      lineColor: '#707073',
      minorGridLineColor: '#505053',
      tickColor: '#707073',
      tickWidth: 1,
      title: {
         style: {
            color: '#A0A0A3'
         }
      }
   },
   tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      style: {
         color: '#F0F0F0'
      }
   },
   plotOptions: {
      series: {
         dataLabels: {
            color: '#B0B0B3'
         },
         marker: {
            lineColor: '#333'
         }
      },
      boxplot: {
         fillColor: '#505053'
      },
      candlestick: {
         lineColor: 'white'
      },
      errorbar: {
         color: 'white'
      }
   },
   legend: {
      itemStyle: {
         color: '#E0E0E3'
      },
      itemHoverStyle: {
         color: '#FFF'
      },
      itemHiddenStyle: {
         color: '#606063'
      }
   },
   credits: {
      style: {
         color: '#666'
      }
   },
   labels: {
      style: {
         color: '#707073'
      }
   },

   drilldown: {
      activeAxisLabelStyle: {
         color: '#F0F0F3'
      },
      activeDataLabelStyle: {
         color: '#F0F0F3'
      }
   },

   navigation: {
      buttonOptions: {
         symbolStroke: '#DDDDDD',
         theme: {
            fill: '#505053'
         }
      }
   },

   // scroll charts
   rangeSelector: {
      buttonTheme: {
         fill: '#505053',
         stroke: '#000000',
         style: {
            color: '#CCC'
         },
         states: {
            hover: {
               fill: '#707073',
               stroke: '#000000',
               style: {
                  color: 'white'
               }
            },
            select: {
               fill: '#000003',
               stroke: '#000000',
               style: {
                  color: 'white'
               }
            }
         }
      },
      inputBoxBorderColor: '#505053',
      inputStyle: {
         backgroundColor: '#333',
         color: 'silver'
      },
      labelStyle: {
         color: 'silver'
      }
   },

   navigator: {
      handles: {
         backgroundColor: '#666',
         borderColor: '#AAA'
      },
      outlineColor: '#CCC',
      maskFill: 'rgba(255,255,255,0.1)',
      series: {
         color: '#7798BF',
         lineColor: '#A6C7ED'
      },
      xAxis: {
         gridLineColor: '#505053'
      }
   },

   scrollbar: {
      barBackgroundColor: '#808083',
      barBorderColor: '#808083',
      buttonArrowColor: '#CCC',
      buttonBackgroundColor: '#606063',
      buttonBorderColor: '#606063',
      rifleColor: '#FFF',
      trackBackgroundColor: '#404043',
      trackBorderColor: '#404043'
   },

   // special colors for some of the
   legendBackgroundColor: 'rgba(0, 0, 0, 0.5)',
   background2: '#505053',
   dataLabelsColor: '#B0B0B3',
   textColor: '#C0C0C0',
   contrastTextColor: '#F0F0F3',
   maskColor: 'rgba(255,255,255,0.3)'
};

// Apply the theme
Highcharts.setOptions(Highcharts.theme);
Highcharts.setOptions({
	global: {
		useUTC: false
	}
});
</script>
    """
    
    if useHighCharts:    #series string here
        print highchart_code % (table)
    else:
        print chart_code % (table[0]) % (table[1])



# print the div that contains the graph
def show_graph():
    print "<h2>Temperature Chart</h2>"
    
    if useHighCharts:
        print '<div id="chart_div" style="min-width: 310px; height: 400px; margin: 0 auto"></div>'
    else:
        print '<div id="chart_div" style="width: 900px; height: 500px;"></div>'



# connect to the db and show some stats
# argument option is the number of hours
def show_stats(option, uom = "C"):

    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
	
    if option is None:
        option = str(24)

    if not demo:
        if uom == "F":
            curs.execute("SELECT timestamp, (MAX(temp) * 9 / 5) + 32 AS temp FROM temps WHERE timestamp>datetime('now','-%s hour') AND timestamp<=datetime('now')" % option)
        else:
            curs.execute("SELECT timestamp,max(temp) FROM temps WHERE timestamp>datetime('now','-%s hour') AND timestamp<=datetime('now')" % option)
    else:
		curs.execute("SELECT timestamp,max(temp) FROM temps WHERE timestamp>datetime('2013-09-19 21:30:02','-%s hour') AND timestamp<=datetime('2013-09-19 21:31:02')" % option)
    
    rowmax=curs.fetchone()
    rowstrmax="{0}&nbsp&nbsp&nbsp{1}{2}".format(str(rowmax[0]),str(rowmax[1]), uom)

    if not demo:
        if uom == "F":
            curs.execute("SELECT timestamp, (MIN(temp) * 9 / 5) + 32 AS temp FROM temps WHERE timestamp>datetime('now','-%s hour') AND timestamp<=datetime('now')" % option)
        else:
            curs.execute("SELECT timestamp,min(temp) FROM temps WHERE timestamp>datetime('now','-%s hour') AND timestamp<=datetime('now')" % option)
    else:
        curs.execute("SELECT timestamp,min(temp) FROM temps WHERE timestamp>datetime('2013-09-19 21:30:02','-%s hour') AND timestamp<=datetime('2013-09-19 21:31:02')" % option)

    rowmin=curs.fetchone()
    rowstrmin="{0}&nbsp&nbsp&nbsp{1}{2}".format(str(rowmin[0]),str(rowmin[1]), uom)

    if not demo:
        if uom == "F":
            curs.execute("SELECT (AVG(temp) * 9 / 5) + 32 AS temp FROM temps WHERE timestamp>datetime('now','-%s hour') AND timestamp<=datetime('now')" % option)
        else:
            curs.execute("SELECT avg(temp) FROM temps WHERE timestamp>datetime('now','-%s hour') AND timestamp<=datetime('now')" % option)
    else:
        curs.execute("SELECT avg(temp) FROM temps WHERE timestamp>datetime('2013-09-19 21:30:02','-%s hour') AND timestamp<=datetime('2013-09-19 21:31:02')" % option)

    rowavg=curs.fetchone()


    print "<hr>"


    print "<h2>Minumum temperature&nbsp</h2>"
    print rowstrmin
    print "<h2>Maximum temperature</h2>"
    print rowstrmax
    print "<h2>Average temperature</h2>"
    print "%.3f" % rowavg+uom

    print "<hr>"

    print "<h2>In the last hour:</h2>"
    print "<table>"
    print "<tr><td><strong>Date/Time</strong></td><td><strong>Temperature</strong></td><td><strong>Device</strong></td></tr>"

    if not demo:
        if uom == "F":
            rows=curs.execute("SELECT timestamp, (temp  * 9 / 5) + 32 AS temp, deviceIdentifier FROM temps\
            WHERE timestamp>datetime('now','-1 hour') AND timestamp<=datetime('now')\
            ORDER BY deviceIdentifier, timestamp DESC")
        else:
            rows=curs.execute("SELECT timestamp, temp, deviceIdentifier FROM temps\
            WHERE timestamp>datetime('now','-1 hour') AND timestamp<=datetime('now')\
            ORDER BY deviceIdentifier, timestamp DESC")
    else:
        rows=curs.execute("SELECT * FROM temps WHERE timestamp>datetime('2013-09-19 21:30:02','-1 hour') AND timestamp<=datetime('2013-09-19 21:31:02')")

    for row in rows:
        rowstr="<tr><td>{0}&emsp;&emsp;</td><td>{1}</td><td>{2}</td></tr>".format(str(row[0]),str(row[1]), str(row[2])
        print rowstr
    print "</table>"

    print "<hr>"

    conn.close()




def print_time_selector(option):

    print """<form action="/cgi-bin/webgui3.py" method="POST">
        Show the temperature logs for  
        <select name="timeinterval">"""


    if option is not None:

        if option == "1":
            print "<option value=\"1\" selected=\"selected\">the last hour</option>"
        else:
            print "<option value=\"1\">the last hour</option>"
            
        if option == "2":
            print "<option value=\"2\" selected=\"selected\">the last 2 hours</option>"
        else:
            print "<option value=\"2\">the last 2 hours</option>"
            
        if option == "6":
            print "<option value=\"6\" selected=\"selected\">the last 6 hours</option>"
        else:
            print "<option value=\"6\">the last 6 hours</option>"

        if option == "12":
            print "<option value=\"12\" selected=\"selected\">the last 12 hours</option>"
        else:
            print "<option value=\"12\">the last 12 hours</option>"

        if option == "24":
            print "<option value=\"24\" selected=\"selected\">the last 24 hours</option>"
        else:
            print "<option value=\"24\">the last 24 hours</option>"

    else:
        print """<option value="1">the last hour</option>
            <option value="2">the last 2 hours</option>
            <option value="6">the last 6 hours</option>
            <option value="12">the last 12 hours</option>
            <option value="24" selected="selected">the last 24 hours</option>"""

    print """        </select>
        <input type="submit" value="Display">
    </form>"""


# check that the option is valid
# and not an SQL injection
def validate_input(option_str):
    # check that the option string represents a number
    if option_str.isalnum():
        # check that the option is within a specific range
        if int(option_str) > 0 and int(option_str) <= 24:
            return option_str
        else:
            return None
    else: 
        return None


#return the option passed to the script
def get_option():
    form=cgi.FieldStorage()
    
    if "timeinterval" in form:
        option = form["timeinterval"].value
        return validate_input (option)
    else:
        return None




# main function
# This is where the program starts 
def main():

    cgitb.enable()

    # get options that may have been passed to this script
    option=get_option()

    uom = "F"
    
    if option is None:
        option = str(2)

    # get data from the database
    records=get_data(option, uom)

    # print the HTTP header
    printHTTPheader()

    if len(records) != 0:
        # convert the data into a table
        table=create_table(records)
    else:
        print "No data found"
        return

    # start printing the page
    print "<html>"
    # print the head section including the table
    # used by the javascript for the chart
    printHTMLHead("Raspberry Pi Temperature Logger", table)

    # print the page body
    print "<body>"
    print "<h1>Raspberry Pi Temperature Logger</h1>"
    print "<hr>"
    print_time_selector(option)
    show_graph()
    show_stats(option, uom)
    print "</body>"
    print "</html>"

    sys.stdout.flush()

if __name__=="__main__":
    main()



