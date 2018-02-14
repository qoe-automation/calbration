#!/usr/bin/env python3

# global imports
import configparser
import optparse
import os
import os.path
import datetime
import codecs
import paramiko
import logging
import time
# local imports
import utils


class QoeExecutor(object):
    def __init__(self, qoe_config, qoe_tests, delay):
        self.conf_file = qoe_config
        self.tests_file = qoe_tests
        self.delay = delay
        parser = configparser.SafeConfigParser()
        with codecs.open(self.conf_file, 'r', encoding='utf-8') as f:
            parser.readfp(f)
        QoeExecutor.read_config(parser)
        self.start = datetime.datetime.now().time()
        self.stop = self.start
        self.test_case_number = 0
        now = datetime.datetime.now()
        day = str(now.day).zfill(2)
        month = str(now.month).zfill(2)
        self.system_date = "{}{}{}".format(month, day, now.year)
        self.utils = utils.Utils()
        try:
            self.vcaf_version = self.utils.get_data_from_url('http://192.168.1.1:8443/management/framework_version')['framework_version']['release']
        except:
            self.vcaf_version = 'N/A'
        self.work_dir = self.system_date + '_' + self.vcaf_version

    @classmethod
    def read_config(cls, parser):
        cls.dut_st_lan = parser.get('DEFAULT', 'dut_st_lan')
        cls.dut_st_lan_mng_ip = parser.get('DEFAULT', 'dut_st_lan_mng_ip')
        cls.dut_st_lan_ip = parser.get('DEFAULT', 'dut_st_lan_ip')
        cls.dut_st_lan_user = parser.get('DEFAULT', 'dut_st_lan_user')
        cls.dut_st_lan_pass = parser.get('DEFAULT', 'dut_st_lan_pass')
        cls.dut_st_wlan = parser.get('DEFAULT', 'dut_st_wlan')
        cls.dut_st_wlan_mng_ip = parser.get('DEFAULT', 'dut_st_wlan_mng_ip')
        cls.dut_st_wlan_ip = parser.get('DEFAULT', 'dut_st_wlan_ip')
        cls.dut_st_wlan_user = parser.get('DEFAULT', 'dut_st_wlan_user')
        cls.dut_st_wlan_pass = parser.get('DEFAULT', 'dut_st_wlan_pass')
        cls.dut_serial_com = parser.get('DEFAULT', 'dut_serial_com')
        cls.dut_ssid = parser.get('DEFAULT', 'dut_ssid')
        cls.dut_wlan_pass = parser.get('DEFAULT', 'dut_wlan_pass')
        cls.int_st_lan = parser.get('DEFAULT', 'int_st_lan')
        cls.int_st_lan_mng_ip = parser.get('DEFAULT', 'int_st_lan_mng_ip')
        cls.int_st_lan_ip = parser.get('DEFAULT', 'int_st_lan_ip')
        cls.int_st_lan_user = parser.get('DEFAULT', 'int_st_lan_user')
        cls.int_st_lan_pass = parser.get('DEFAULT', 'int_st_lan_pass')
        cls.int_st_wlan = parser.get('DEFAULT', 'int_st_wlan')
        cls.int_st_wlan_mng_ip = parser.get('DEFAULT', 'int_st_wlan_mng_ip')
        cls.int_st_wlan_ip = parser.get('DEFAULT', 'int_st_wlan_ip')
        cls.int_st_wlan_user = parser.get('DEFAULT', 'int_st_wlan_user')
        cls.int_st_wlan_pass = parser.get('DEFAULT', 'int_st_wlan_pass')
        cls.int_serial_com = parser.get('DEFAULT', 'int_serial_com')
        cls.int_ssid = parser.get('DEFAULT', 'int_ssid')
        cls.int_wlan_pass = parser.get('DEFAULT', 'int_wlan_pass')
        cls.duration = parser.get('DEFAULT', 'duration')
        cls.tolerance = parser.get('DEFAULT', 'tolerance')
        cls.period = parser.get('DEFAULT', 'period')
        cls.url = parser.get('DEFAULT', 'url')
        cls.iperf_path = parser.get('DEFAULT', 'iperf_path')
        cls.iperf_results_dir = parser.get('DEFAULT', 'iperf_results_dir')

    def exit_when_done(self):
        msg = "Start time: {}\nEnd time: {}\nExiting...".format(self.start, self.stop)
        self.utils.exit_when_done(msg)

    def reboot_routers_via_serial_com(self):
        cmds_list = ['exit', 'exit', 'exit', 'admin\radmin\radmin', 'admin\radmin\radmin', 'admin\radmin\radmin',
                     'admin\radmin\radmin', 'system reboot']
        self.utils.write2serial(self.dut_serial_com, 115200, cmds_list)
        self.utils.write2serial(self.int_serial_com, 115200, cmds_list)
        time.sleep(360)

    def set_interferrer_2_4_channel(self, int_channel):
        cmds_list = ['exit', 'exit', 'exit', 'admin\radmin\radmin', 'admin\radmin\radmin', 'admin\radmin\radmin',
                     'admin\radmin\radmin',
                     'cwmp set_params InternetGatewayDevice.LANDevice.5.WLANConfiguration.9.Channel {}'.format(
                         int_channel)]
        self.utils.write2serial(self.int_serial_com, 115200, cmds_list)

    def start_iperf_server(self, host_name, user_name, password):
        cmd = "/usr/bin/nohup {} -s  > /dev/null 2>&1 &".format(self.iperf_path)
        rc, stdout_ = self.utils.run_cmd_via_ssh(host_name, user_name, password, cmd)
        if rc:
            raise Exception("Failed to start iperf server on {}\nExiting...".format(host_name))

    def start_iperf_client(self, host_name, user_name, password, data, work_dir, scenario_id, fn_suf, st_lan_ip):
        dest_dir = self.iperf_results_dir + '/' + work_dir
        cmd = "/usr/bin/test -d {} || /bin/mkdir -p {}".format(dest_dir, dest_dir)
        rc, stdout_ = self.utils.run_cmd_via_ssh(host_name, user_name, password, cmd)
        if rc: raise Exception("Failed to run '{}' on {}\nExiting...".format(cmd, host_name))
        fn = dest_dir + "/{}_{}".format(scenario_id, fn_suf)
        cmd = "/usr/bin/nohup {} -c {} -t {} -u -i 1 --get-server-output -b {}K   > {} 2>&1 &".format(self.iperf_path,
                                                                                                      st_lan_ip,
                                                                                                      self.duration,
                                                                                                      data, fn)
        rc, stdout_ = self.utils.run_cmd_via_ssh(host_name, user_name, password, cmd)
        time.sleep(5)

    def stop_iperf(self, host_name, user_name, password):
        cmd = "/usr/bin/killall iperf3"
        rc, stdout_ = self.utils.run_cmd_via_ssh(host_name, user_name, password, cmd, retry=False)
        time.sleep(3)
        # if rc:
        #    raise Exception("Failed to stop iperf on {}\nExiting...".format(host_name))

    def connect_to_wifi_ssid(self, host, host_user, host_password, req_wifi_ssid, wlan_ssid_password):
        cmd = "/sbin/iwgetid -r"
        rc, stdout_ = self.utils.run_cmd_via_ssh(host, host_user, host_password, cmd)
        if rc:
            raise Exception("Failed to run '{}' on {}\nExiting...".format(cmd, host))
        if stdout_.strip() != req_wifi_ssid:
            cmd = "/usr/bin/nmcli dev wifi connect {} password {}".format(req_wifi_ssid, wlan_ssid_password)
            rc, stdout_ = self.utils.run_cmd_via_ssh(host, host_user, host_password, cmd)
            if rc:
                raise Exception("Failed to connect to wifi ssid {} on {}\nExiting...".format(req_wifi_ssid, host))

    def get_qoe_tests_data_info(self):
        fh = open(self.tests_file, 'r')
        for line in fh:
            if not line: yield []
            data = line.split(',')
            data = [int(item.strip()) for item in data]
            ret_val = data
            # [test id, dut_channel, dut_data, int_channel, int_data]
            yield ret_val
	
    def wifi_reconnect(self, host, host_user, host_password):
        cmd = "/bin/bash /qoe/wifi-reconnect.sh"
        rc, stdout_ = self.utils.run_cmd_via_ssh(host, host_user, host_password, cmd)
        time.sleep(10)

    def run_scenario(self, dut_data, dut_channel, int_data, int_channel, test_id):
        scenario_id = "TP{}_dut_ch{}_{}_int_ch{}_{}".format(test_id, dut_channel, dut_data, int_channel, int_data)
        self.stop_iperf(self.dut_st_wlan_mng_ip,self.dut_st_wlan_user, self.dut_st_wlan_pass)
        self.wifi_reconnect(self.dut_st_wlan_mng_ip, self.dut_st_wlan_user, self.dut_st_wlan_pass)
        self.start_iperf_server(self.dut_st_wlan_mng_ip, self.dut_st_wlan_user, self.dut_st_wlan_pass)
        if dut_data > 0:
            self.start_iperf_client(self.dut_st_lan_mng_ip, self.dut_st_lan_user, self.dut_st_lan_pass, dut_data,
                                    self.work_dir, scenario_id, 'iperf3_dut_st_wlan.log', self.dut_st_wlan_ip)
        self.stop_iperf(self.int_st_wlan_mng_ip, self.int_st_wlan_user, self.int_st_wlan_pass)
        self.wifi_reconnect(self.int_st_wlan_mng_ip, self.int_st_wlan_user, self.int_st_wlan_pass)
        self.start_iperf_server(self.int_st_wlan_mng_ip, self.int_st_wlan_user, self.int_st_wlan_pass)
        if int_data > 0:
            self.start_iperf_client(self.int_st_lan_mng_ip, self.int_st_lan_user, self.int_st_lan_pass, int_data,
                                    self.work_dir, scenario_id, 'iperf3_int_st_wlan.log', self.int_st_wlan_ip)

        cmd = "python mini_data_collector.py --dut-bitrate {} ".format(dut_data)
        cmd += "--external-ap-load {} ".format(int_data)
        cmd += "--external-ap-channel {} ".format(int_channel)
        cmd += "--duration {} ".format(self.duration)
        cmd += "--period {} ".format(self.period)
        cmd += "--tolerance {} ".format(self.tolerance)
        cmd += "--url {} ".format(self.url)
        cmd += "--output {}/{}".format(self.work_dir, scenario_id)
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)

        self.utils.log(logging.INFO, "waiting for {}sec before data collection...".format(self.delay))
        time.sleep(self.delay)

        rc = os.system(cmd)
        # if rc:
        #    raise Exception("mini_data_collector script finished with error code {}\nExiting...".format(rc))

        self.utils.log(logging.INFO, "iperf client will be stopped in 3 sec...")
        time.sleep(3)

        self.stop_iperf(self.dut_st_lan_mng_ip, self.dut_st_lan_user, self.dut_st_lan_pass)
        self.stop_iperf(self.int_st_lan_mng_ip, self.int_st_lan_user, self.int_st_lan_pass)

    def run(self):
        test_data_gen = self.get_qoe_tests_data_info()
        try:
            while True:
                test_data_list = next(test_data_gen)
                if len(test_data_list) == 0:
                    break
                test_id, dut_channel, dut_data, int_channel, int_data = test_data_list[0], test_data_list[1], \
                                                                        test_data_list[2], test_data_list[3], \
                                                                        test_data_list[4]
                # test id, dut_channel, dut_data, int_channel, int_data]
                self.set_interferrer_2_4_channel(int_channel)
                self.run_scenario(dut_data, dut_channel, int_data, int_channel, test_id)
                self.test_case_number += 1
                if self.test_case_number % 5 == 0:
                    self.reboot_routers_via_serial_com()

        finally:
            self.stop_iperf(self.dut_st_wlan_mng_ip, self.dut_st_wlan_user, self.dut_st_wlan_pass)
            self.stop_iperf(self.int_st_wlan_mng_ip, self.int_st_wlan_user, self.int_st_wlan_pass)


def main():
    parser = optparse.OptionParser()
    parser.add_option('--config', dest='qoe_config', type="string", default='qoe_executor.cfg',
                      help='path to QoE executor configuration file, default: qoe_executor.cfg (optional)')
    parser.add_option('--tests', dest='qoe_tests', type="string", default='tests.csv',
                      help='path to QoE executor tests file, default: tests.csv (optional)')
    parser.add_option('--delay-before-start', dest='delay', type="int", default=0,
                      help='delay before data collection start, default 10sec (optional)')
    (opts, args) = parser.parse_args()
    assert os.path.isfile(opts.qoe_config) and os.path.exists(opts.qoe_config), \
        "--config {} not a file or not exists.".format(opts.qoe_config)
    assert os.path.isfile(opts.qoe_tests) and os.path.exists(opts.qoe_tests), \
        "--tests {} not a file or not exists.".format(opts.qoe_tests)
    qoe_executor = QoeExecutor(qoe_config=opts.qoe_config, qoe_tests=opts.qoe_tests, delay=opts.delay)
    qoe_executor.utils.log(logging.INFO, "Running with arguments:")
    qoe_executor.utils.log(logging.INFO, "--config {}".format(qoe_executor.conf_file))
    qoe_executor.utils.log(logging.INFO, "--tests {}".format(qoe_executor.tests_file))
    qoe_executor.utils.log(logging.INFO, "--delay-before-start {}".format(qoe_executor.delay))
    qoe_executor.utils.log(logging.INFO, "(Ctrl+C to exit)\n")
    try:
        qoe_executor.run()
    except KeyboardInterrupt:
        qoe_executor.stop = datetime.datetime.now().time()
        qoe_executor.exit_when_done()


if __name__ == "__main__":
    main()
