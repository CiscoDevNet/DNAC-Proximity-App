import requests
import time
from datetime import datetime
import datetime as dt
from weasyprint import HTML
from shutil import copyfile
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
table_data = ''


def handle(event, context):
    logger.info('### EVENT INFO \n {}'.format(json.dumps(event)))
    if 'detail-type' in event:
        logger.info('### KEEP ALIVE FUNCTION')
    else:
        dnac_proximity_data(event)
        build_html_file()


def convert_epoch(epoch):
    epoch = int(epoch)
    s, ms = divmod(epoch, 1000)
    timestamp = time.strftime("%d %b %Y %H:%M:%S", time.localtime(s))
    return timestamp


def exposure_time(start_time_ep, end_time_ep):
    date_fmt = '%Y-%m-%d %H:%M:%S'
    start_stamp = ''
    end_stamp = ''
    exp_time_ep = {'start': int(start_time_ep), 'end': int(end_time_ep)}
    for key, time_ep in exp_time_ep.items():
        s, ms = divmod(time_ep, 1000)
        timestamp = time.strftime(date_fmt, time.localtime(s))
        if key == 'start':
            start_stamp = datetime.strptime(timestamp, date_fmt)
        else:
            end_stamp = datetime.strptime(timestamp, date_fmt)
    td = end_stamp - start_stamp
    time_diff = int(round(td.total_seconds()))
    return str(dt.timedelta(seconds=time_diff))


def report_html_aside(user, r_start_date, r_end_date, r_days, exp_time):
    global aside
    aside = '<aside>\n<data id="from">\n'
    aside += "Today's Date: {}\n".format(datetime.today().strftime("%a, %d %b %Y"))
    aside += "Pandemic Positive Employee: {}\n".format(user)
    aside += "Report Date: {} - {}\n".format(r_start_date, r_end_date)
    aside += "Report Range: {} days\n".format(r_days)
    aside += "Exposure Time: {} min\n".format(exp_time)
    aside += "</data>\n</aside>\n"


def report_table_data(client_user, client_mac, client_device, expo_time, location):
    global table_data
    table_data += "<tr>\n"
    table_data += "<td>{}</td>\n".format(client_user)
    table_data += "<td>{}</td>\n".format(client_mac)
    table_data += "<td>{}</td>\n".format(client_device)
    table_data += "<td>{}</td>\n".format(expo_time)
    table_data += "</tr>\n"


def report_html_table():
    table_header = "<table>\n<thead>\n<th>Username</th>\n<th>Device MacAddress</th>" \
                   "\n<th>Device Type</th>\n<th>Exposure Time</th>\n</thead><tbody>\n"
    table_footer = "</tbody>\n</table>"
    table = table_header + table_data + table_footer
    return table


def build_html_file():
    html_file = "personnel_report.html"
    copyfile('report_header.html', 'personnel_report.html')
    table = report_html_table()
    content = aside + table
    content += "</body>\n</html>"
    with open(html_file, 'a') as newHTMLFile:
        newHTMLFile.write(content)
        newHTMLFile.close()
    write_pdf(html_file)


def write_pdf(html_file):
    HTML(html_file).write_pdf('tmp/contact-tracing-report.pdf')


def dnac_proximity_data():
    tracing_data = requests.get(url="https://a0r4cjdtt7.execute-api.us-west-1.amazonaws.com/proximity/data/kevinm")
    report_html_aside(user=tracing_data.json()['details']['user_name'],
                      r_start_date= convert_epoch(tracing_data.json()['details']['start_time']),
                      r_end_date= convert_epoch(tracing_data.json()['details']['end_time']),
                      r_days= tracing_data.json()['details']['number_days'],
                      exp_time=tracing_data.json()['details']['time_resolution']
                      )
    for client_proximity in tracing_data.json()['details']['client_proximity']:
        for client_info in client_proximity['client_info']:
            for client in client_info['users_info']:
                if 'client_user' in client:
                    report_table_data(client['client_user'], client['client_mac'], client['client_type'],
                                      exposure_time(client_info['start_time'], client_info['end_time']),
                                      client_info['location'])
