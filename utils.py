import ssl
import sys
import time
import json
import urllib.request
import urllib.parse
import serial
import paramiko
#import wmi
import logging


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Utils(object):
    @classmethod
    def write2file(cls, fn, mode, data, sep='\n'):
        with open(fn, mode=mode) as data_file:
            data_file.write(data + sep)

    @classmethod
    def get_data_from_url(cls, url):
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=context) as response:
                data = json.loads(response.read().decode('utf8'))
        except Exception as err:
            err_msg = "An error occurred during attempt to retrieve data from {}:\n{}".format(url, str(err))
            print(err_msg)
            #Utils.exit_with_err(err_msg)
            return {}
        return data

    @classmethod
    def exit_with_err(cls, err_msg):
        print(err_msg)
        sys.exit(1)

    @classmethod
    def exit_when_done(cls, msg):
        print(msg)
        sys.exit(0)

    @classmethod
    def run_time_in_sec(cls, t2, t1):
        time1 = (t1.hour * 60 + t1.minute) * 60 + t1.second
        time2 = (t2.hour * 60 + t2.minute) * 60 + t2.second
        return time2 - time1

    @classmethod
    def log(cls, log_level, msg):
        logger.log(log_level, msg)

    @classmethod
    def write2serial(cls, port, baudrate, commands_list):
        ser = serial.Serial(port, baudrate)
        ser.isOpen()
        for cmd in commands_list:
            ser.write((cmd + '\r\n').encode())
            user_info = 'Serial request: {}\tSerial response: '.format(cmd)
            time.sleep(1)
            while ser.inWaiting() > 0:
                user_info += ser.read(1).decode('utf-8')
            Utils.log(logging.DEBUG, user_info)
        ser.close()

    @classmethod
    def run_cmd_via_ssh(cls, hostname, username, password, cmd, port=22, retry=True):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, password=password)
        for i in range(3):
            Utils.log(logging.DEBUG, "running '{}' on {} (try #{})".format(cmd, hostname, i))
            stdin_, stdout_, stderr_ = client.exec_command(cmd)
            rc = stdout_.channel.recv_exit_status()
            stdout_, stderr_ = stdout_.read(), stderr_.read()
            Utils.log(logging.DEBUG, "stdout: {}\nstderr: {}".format(stdout_, stderr_))
            Utils.log(logging.DEBUG, "exit status: {}".format(rc))
            if rc == 0 or i == 2 or not retry:
                break
            Utils.log(logging.DEBUG, "waiting for 20sec before retry...")
            time.sleep(20)
        client.close()
        return rc, stdout_

    @classmethod
    def wmi_connection(cls, server, username, password):
        Utils.log(logging.DEBUG, "attempting to connect with " + server + '...')
        return wmi.WMI(server, user=username, password=password)
