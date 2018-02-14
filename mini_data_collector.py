#!/usr/bin/env python3

# global imports
from optparse import OptionParser
import urllib.request
import urllib.parse
import json
import sys
import time
import datetime
import ssl
import logging
# local imports
import utils


class Units(object):
    UNITS_DICT = {'tx_in_net_sec': '[sec]',
                  'datarate': '[Kbps]',
                  'rtr': '[%]',
                  'tx_data_total': '[packets]',
                  'rx_data_total': '[packets]',
                  'tx_bytes_total': '[B]',
                  'rx_bytes_total': '[B]',
                  'bandwidth': '[GHz]',
                  'tx_phyrate_raw': '[Kbps]',
                  'tx_phyrate_avg': '[Kbps]',
                  'air_load': '[%]',
                  'interference': '[%]',
                  'txop': '[%]',
                  'noise': '[dB]',
                  'ap_load': '[%]',
                  'total_rx_bytes': '[B]',
                  'total_tx_bytes': '[B]',
                  'tx_phyrate_score': '[%]',
                  'tx_retry_score': '[%]',
                  'tx_link_quality_score': '[%]',
                  'tx_link_effective_quality_score': '[%]',
                  'channel_cca_user_impact': '[%]',
                  'channel_load': '[%]',
                  'channel_noise': '[%]',
                  'tx_ineff': '[%]',
                  'channel_cca_score': '[%]',
                  'tx_bytes_total': '[B]'}

    WIFI_HEADERS_DICT = {'/wifi_scoring/air_data': ["band",
                                                    "num_of_samples",
                                                    "channel_load",
                                                    "interference",
                                                    "channel_noise",
                                                    "tx_ineff",
                                                    "channel_cca_score",
                                                    "channel"],
                         '/wifi_scoring/link_data': ["tx_link_quality_score",
                                                     "tx_link_effective_quality_score",
                                                     "link_quality_level",
                                                     "channel_cca_user_impact",
                                                     "tx_phyrate_score",
                                                     "tx_retry_score",
                                                     "tx_failure_score",
                                                     "num_of_samples",
                                                     "hostname",
                                                     "host_type",
                                                     "mac_address",
                                                     "band"],
                         '/wifi_monitoring/link_data': ["mac_address",
                                                        "tx_data_total",
                                                        "rx_data_total",
                                                        "tx_retry_total",
                                                        "tx_bytes_total",
                                                        "rx_bytes_total",
                                                        "tx_in_net_sec",
                                                        "num_of_samples",
                                                        "tx_phyrate_avg",
                                                        "rssi",
                                                        "datarate",
                                                        "rtr",
                                                        "bandwidth",
                                                        "is_ldpc",
                                                        "sgi",
                                                        "tx_nss",
                                                        "throughput_level",
                                                        "band",
                                                        "tx_phyrate_raw",
                                                        "timestamp"],
                         '/wifi_monitoring/air_data': ["band",
                                                       "status",
                                                       "air_load",
                                                       "interference",
                                                       "channel",
                                                       "txop",
                                                       "noise",
                                                       "glitch",
                                                       "badplcp",
                                                       "timestamp"],
                         '/wifi_monitoring/ap_data': ["band",
                                                      "status",
                                                      "ap_load",
                                                      "channel",
                                                      "bandwidth",
                                                      "radar_status",
                                                      "radar_detected_channel",
                                                      "tx_bytes_total",
                                                      "rx_bytes_total",
                                                      "timestamp"]
                         }

    SUMMARY_HEADER = ['time [sec]',                          # calculated
                      'nominal bit rate [Kbps]',             # --dut-bitrate (from cmd)
                      'external AP load [Kbps]',             # --external-ap-load (from cmd)
                      'external AP channel',                 # --external-ap-channel (from cmd)
                      'actual bitrate loss [%]',             # calculated
                      'delta [%] (tx_link_effective_quality_score-actual bitrate loss)', # calculated
                      'test result',                         # calculated

                      'tx_link_effective_quality_score [%]', # /wifi_scoring/link_data
                      'tx_link_quality_score [%]',           # /wifi_scoring/link_data
                      'tx_retry_score [%]',                  # /wifi_scoring/link_data
                      'tx_phyrate_score [%]',                # /wifi_scoring/link_data
                      'channel_cca_user_impact [%]',         # /wifi_scoring/link_data

                      'channel',                             # /wifi_scoring/air_data
                      'channel_cca_score [%]',               # /wifi_scoring/air_data
                      'channel_load [%]',                    # /wifi_scoring/air_data
                      'tx_ineff [%]',                        # /wifi_scoring/air_data
                      'channel_noise [%]',                   # /wifi_scoring/air_data
                      'wifi_scoring/air_data.interference [%]',

                      'datarate [Kbps]',                     # /wifi_monitoring/link_data
                      'rtr [%]',                             # /wifi_monitoring/link_data
                      'tx_phyrate_avg [Kbps]',               # /wifi_monitoring/link_data
                      'tx_bytes_total [B]',                  # /wifi_monitoring/link_data
                      'rssi',                                # /wifi_monitoring/link_data

                      'air_load [%]',                        # /wifi_monitoring/air_data
                      'txop [%]',                            # /wifi_monitoring/air_data
                      'noise [dB]',                          # /wifi_monitoring/air_data
                      'wifi_monitoring/air_data.interference [%]']

    SUMMARY_DICT = {'actual bitrate loss [%]': 0,
                    'delta [%] (tx_link_effective_quality_score-actual bitrate loss)': 0,
                    'tx_link_effective_quality_score [%]': 0,
                    'tx_link_quality_score [%]': 0,
                    'tx_retry_score [%]': 0,
                    'tx_phyrate_score [%]': 0,
                    'channel_cca_user_impact [%]': 0,
                    'channel_cca_score [%]': 0,
                    'channel_load [%]': 0,
                    'tx_ineff [%]': 0,
                    'channel_noise [%]': 0,
                    'wifi_scoring/air_data.interference [%]': 0,
                    'datarate [Kbps]': 0,
                    'rtr [%]': 0,
                    'tx_phyrate_avg [Kbps]': 0,
                    'tx_bytes_total [B]': 0,
                    'rssi' :0,
                    'air_load [%]': 0,
                    'txop [%]': 0,
                    'noise [dB]': 0,
                    'wifi_monitoring/air_data.interference [%]':0}

    TEMP_DICT = {'actual bitrate loss [%]': 0,
                 'delta [%] (tx_link_effective_quality_score-actual bitrate loss)': 0,
                 'tx_link_effective_quality_score [%]': 0,
                 'tx_link_quality_score [%]': 0,
                 'tx_retry_score [%]': 0,
                 'tx_phyrate_score [%]': 0,
                 'channel_cca_user_impact [%]': 0,
                 'channel_cca_score [%]': 0,
                 'channel_load [%]': 0,
                 'tx_ineff [%]': 0,
                 'channel_noise [%]': 0,
                 'wifi_scoring/air_data.interference [%]': 0,
                 'datarate [Kbps]': 0,
                 'rtr [%]': 0,
                 'tx_phyrate_avg [Kbps]': 0,
                 'tx_bytes_total [B]': 0,
                 'rssi': 0,
                 'air_load [%]': 0,
                 'txop [%]': 0,
                 'noise [dB]': 0,
                 'wifi_monitoring/air_data.interference [%]': 0}


class Tool(object):
    url_sfxs = ['/wifi_monitoring/air_data', '/wifi_monitoring/ap_data',
                '/wifi_monitoring/link_data', '/wifi_scoring/air_data',
                '/wifi_scoring/link_data']

    def __init__(self, url_val, period_val, output_file_val, dut_bitrate, external_ap_load,
                 external_ap_channel, tolerance, duration):
        self.url = url_val
        self.period = period_val
        self.output_file = output_file_val if output_file_val.endswith('.csv') else output_file_val + '.csv'
        self.error_file = 'errors.log'
        self.dut_bitrate = dut_bitrate
        self.external_ap_load = external_ap_load
        self.external_ap_channel = external_ap_channel
        self.tolerance = tolerance
        self.duration = duration
        self.suf_list = []
        self.keys = []
        self.utils = utils.Utils()
        self.start = datetime.datetime.now().time()
        self.stop = self.start
        self.num_of_iter = 0

    def exit_when_done(self):
        msg = "Start time: {}\nEnd time: {}".format(self.start, self.stop)
        msg += "\nThe tool was terminated after {} iteration(s).\nExiting...".format(self.num_of_iter)
        self.utils.exit_when_done(msg)

    @classmethod
    def construct_fn(cls, curr_url, suf):
        name = curr_url[1:].replace('/', '.')
        return "{}_{}.csv".format(name, suf)

    @classmethod
    def get_headers_for_wifi_monitoring_ap_data_or_wifi_monitoring_air_data(cls, data, suf):
        try:
            keys_list = data[suf][0].keys()
        except:
            keys_list = []
        return keys_list

    @classmethod
    def get_headers_for_wifi_monitoring_link_data(cls, data, suf):
        try:
            k = list(data[suf][0].keys())[0]
            keys_list = list(data[suf][0][k].keys())
        except:
            keys_list = []
        return keys_list

    @classmethod
    def get_headers_for_wifi_scoring_air_data(cls, data, suf):
        try:
            keys_list = data[0].keys()
        except:
            keys_list = []
        return keys_list

    @classmethod
    def get_headers_for_wifi_scoring_link_data(cls, data, suf):
        try:
            keys_list = data[0].keys()
        except:
            keys_list = []
        return keys_list

    def prepare_data_for_wifi_monitoring_ap_data_or_wifi_monitoring_air_data(self, fn, data, suf, url_suf):
        for d in data[suf]:
            row_list = []
            flag = 0
            for k in Units.WIFI_HEADERS_DICT[url_suf]:
                if k in d:
                    row_list.append(str(d[k]))
                else:
                    flag = 1
                    break
            if flag: continue
            row = ','.join(row_list)
            self.utils.write2file(fn, 'a', row)
            return # get only the 1st line

    def prepare_data_for_wifi_monitoring_link_data(self, fn, data, suf, url_suf):
        for d in data[suf]:
            try:
                row_list = []
                if len(list(d.keys())):
                    dk = list(d.keys())[0]
                    target_dict = d[dk]
                    for k in Units.WIFI_HEADERS_DICT[url_suf]:
                        if k in target_dict:
                            row_list.append(str(target_dict[k]))
                        else:
                            raise
                else:
                    continue
                row = ','.join(row_list)
                self.utils.write2file(fn, 'a', row)
                return # get only the 1st line with data
            except:
                pass

    def prepare_data_for_wifi_scoring_air_data(self, fn, data, suf, url_suf):
        ndx = 0 if suf == '2.4GHz' else 1
        row_list = []
        for k in Units.WIFI_HEADERS_DICT[url_suf]:
            if k in data[ndx]:
                row_list.append(str(data[ndx][k]))
            else:
                return
        row = ','.join(row_list)
        self.utils.write2file(fn, 'a', row)

    def prepare_data_for_wifi_scoring_link_data(self, fn, data, suf, url_suf):
        row_list = []
        for k in Units.WIFI_HEADERS_DICT[url_suf]:
            if k in data[0]:
                row_list.append(str(data[0][k]))
            else:
                return
        row = ','.join(row_list)
        self.utils.write2file(fn, 'a', row)

    @classmethod
    def update_units(cls, ks):
        ret_list = []
        for k in ks:
            ret_list.append(k + ' ' + Units.UNITS_DICT.get(k, ''))
        return ret_list

    def prepare_headers(self, data, curr_url, sfx):
        for suf in self.suf_list:
            fn = Tool.construct_fn(sfx, suf)
            if curr_url.endswith('/wifi_monitoring/air_data') or curr_url.endswith('/wifi_monitoring/ap_data'):
                ks = Tool.get_headers_for_wifi_monitoring_ap_data_or_wifi_monitoring_air_data(data, suf)
            elif curr_url.endswith('/wifi_monitoring/link_data'):
                ks = Tool.get_headers_for_wifi_monitoring_link_data(data, suf)
            elif curr_url.endswith('/wifi_scoring/air_data'):
                ks = Tool.get_headers_for_wifi_scoring_air_data(data, suf)
            elif curr_url.endswith('/wifi_scoring/link_data'):
                ks = Tool.get_headers_for_wifi_scoring_link_data(data, suf)
            else:
                ks = []

            headers = Units.WIFI_HEADERS_DICT[sfx]
            ks = Tool.update_units(headers)
            headers = ','.join(ks)
            self.utils.write2file(fn, 'w', headers)

    def prepare_data(self, data, curr_url, url_sfx):
        for suf in self.suf_list:
            fn = Tool.construct_fn(url_sfx, suf)
            if not data:
                vec_na = ["N/A"] * len(Units.WIFI_HEADERS_DICT[url_sfx])
                row_na =','.join(vec_na)
                self.utils.write2file(fn, 'a', row_na)
            elif curr_url.endswith('/wifi_monitoring/air_data') or curr_url.endswith('/wifi_monitoring/ap_data'):
                self.prepare_data_for_wifi_monitoring_ap_data_or_wifi_monitoring_air_data(fn, data, suf, url_sfx)
            elif curr_url.endswith('/wifi_monitoring/link_data'):
                self.prepare_data_for_wifi_monitoring_link_data(fn, data, suf, url_sfx)
            elif curr_url.endswith('/wifi_scoring/air_data'):
                self.prepare_data_for_wifi_scoring_air_data(fn, data, suf, url_sfx)
            elif curr_url.endswith('/wifi_scoring/link_data'):
                self.prepare_data_for_wifi_scoring_link_data(fn, data, suf, url_sfx)
            else:
                pass

    def run(self):
        for sfx in Tool.url_sfxs:
            curr_url = urllib.parse.urljoin(self.url, sfx)
            data = self.utils.get_data_from_url(curr_url)
            self.suf_list = data.keys() if isinstance(data, dict) else ['2.4GHz', '5GHz'] if len(data) == 2 else ['2.4GHz']
            self.prepare_headers(data, curr_url, sfx)
            self.prepare_data(data, curr_url, sfx)

        while True:
            time.sleep(self.period)
            self.num_of_iter += 1
            for sfx in Tool.url_sfxs:
                curr_url = urllib.parse.urljoin(self.url, sfx)
                data = self.utils.get_data_from_url(curr_url)
                self.suf_list = data.keys() if isinstance(data, dict) else ['2.4GHz', '5GHz'] if len(data) == 2 else ['2.4GHz']
                self.prepare_data(data, curr_url, sfx)
            if self.utils.run_time_in_sec(datetime.datetime.now().time(), self.start) >= self.duration:
                return KeyboardInterrupt

    def generate_summary_headers(self, output_fn):
        summary_hdr = ','.join(Units.SUMMARY_HEADER)
        self.utils.write2file(output_fn, 'w', summary_hdr)

    @classmethod
    def get_wifi_scoring_link_data_info(cls, suf, cnt):
        fn = Tool.construct_fn('/wifi_scoring/link_data', suf)
        fh = open(fn, 'r')
        if not cnt: fh.readline()
        for line in fh:
            if not line: yield '', ''
            data = line.split(',')
            data = [item.strip() for item in data]
            ret_val = data[1] + ',' + data[0] + ',' + data[5] + ',' + data[4] + ',' + data[3] + ','
            # tx_link_effective_quality_score [%], tx_link_quality_score [%], tx_retry_score [%], tx_phyrate_score [%], channel_cca_user_impact [%]
            try:
                Units.TEMP_DICT['tx_link_effective_quality_score [%]'] = float(data[1])
                Units.TEMP_DICT['tx_link_quality_score [%]'] = float(data[0])
                Units.TEMP_DICT['tx_retry_score [%]'] = float(data[5])
                Units.TEMP_DICT['tx_phyrate_score [%]'] = float(data[4])
                Units.TEMP_DICT['channel_cca_user_impact [%]'] = float(data[3])
            except:
                pass
            yield ret_val, data[1]

    @classmethod
    def get_wifi_scoring_air_data_info(cls, suf, cnt):
        fn = Tool.construct_fn('/wifi_scoring/air_data', suf)
        fh = open(fn, 'r')
        if not cnt: fh.readline()
        for line in fh:
            if not line: yield ''
            data = line.split(',')
            data = [item.strip() for item in data]
            ret_val = data[7] + ',' + data[6] + ',' + data[2] + ',' + data[5] + ',' + data[4] + ',' + data[3] + ','
            # channel, channel_cca_score [%], channel_load [%], tx_ineff [%], channel_noise [%], wifi_scoring/air_data.interference [%]
            try:
                Units.TEMP_DICT['channel_cca_score [%]'] = float(data[6])
                Units.TEMP_DICT['channel_load [%]'] = float(data[2])
                Units.TEMP_DICT['tx_ineff [%]'] = float(data[5])
                Units.TEMP_DICT['channel_noise [%]'] = float(data[4])
                Units.TEMP_DICT['wifi_scoring/air_data.interference [%]'] = float(data[3])
            except:
                pass
            yield ret_val

    @classmethod
    def get_wifi_monitoring_link_data_info(cls, suf, cnt):
        fn = Tool.construct_fn('/wifi_monitoring/link_data', suf)
        fh = open(fn, 'r')
        if not cnt: fh.readline()
        for line in fh:
            if not line: yield '', ''
            data = line.split(',')
            data = [item.strip() for item in data]
            ret_val = data[10] + ',' + data[11] + ',' + data[8] + ',' + data[4] + ',' + data[9] + ','
            # datarate [Kbs], rtr [%], tx_phyrate_avg [Kbs], tx_bytes_total [Bytes], rssi
            try:
                Units.TEMP_DICT['datarate [Kbps]'] = float(data[10])
                Units.TEMP_DICT['rtr [%]'] = float(data[11])
                Units.TEMP_DICT['tx_phyrate_avg [Kbps]'] = float(data[8])
                Units.TEMP_DICT['tx_bytes_total [B]'] = float(data[4])
                Units.TEMP_DICT['rssi'] = float(data[9])
            except:
                pass
            yield ret_val, data[10]

    @classmethod
    def get_wifi_monitoring_air_data_info(cls, suf, cnt):
        fn = Tool.construct_fn('/wifi_monitoring/air_data', suf)
        fh = open(fn, 'r')
        if not cnt: fh.readline()
        for line in fh:
            if not line: yield ''
            data = line.split(',')
            data = [item.strip() for item in data]
            ret_val = data[2] + ',' + data[5] + ',' + data[6] + ',' + data[3]
            # air_load [%], txop [%], noise [dB], wifi_monitoring/air_data.interference [%]
            try:
                Units.TEMP_DICT['air_load [%]'] = float(data[2])
                Units.TEMP_DICT['txop [%]'] = float(data[5])
                Units.TEMP_DICT['noise [dB]'] = float(data[6])
                Units.TEMP_DICT['wifi_monitoring/air_data.interference [%]'] = float(data[3])
            except:
                pass
            yield ret_val

    def get_args_from_cmd(self):
        ret_val = str(self.dut_bitrate) + ',' + str(self.external_ap_load) + ', ' + str(self.external_ap_channel) + ','
        # nominal bit rate [Mbs], external AP load [Mbs], external AP channel
        return ret_val

    @classmethod
    def reset_temp_res_dict(cls):
        for k in Units.TEMP_DICT.keys():
            Units.TEMP_DICT[k] = 0

    @classmethod
    def accumulate_temp_results(cls, actual_bitrate_loss_val):
        for k in Units.SUMMARY_DICT.keys():
            if k == 'actual bitrate loss [%]':
                Units.SUMMARY_DICT[k] += actual_bitrate_loss_val
            else:
                Units.SUMMARY_DICT[k] += Units.TEMP_DICT[k]

    def prepare_avg_row(self, num_of_records_for_avg, delta_total):
        res = ""
        delta_avg = 0
        if num_of_records_for_avg == 0:
            return "N/A," * 26 + "N/A"
        for k in Units.SUMMARY_HEADER:
            if k == 'delta [%] (tx_link_effective_quality_score-actual bitrate loss)':
                delta_avg = delta_total / num_of_records_for_avg
                res += str(delta_avg) + ','
            elif k == 'test result':
                res += 'Passed!,' if abs(delta_avg) <= self.tolerance else 'Failed!,'
            elif k in Units.SUMMARY_DICT:
                res += str(Units.SUMMARY_DICT[k]/num_of_records_for_avg) + ','
            else:
                res += ','
        return res

    def generate_summary(self):
        for suf in self.suf_list:
            output_fn = '.'.join(self.output_file.split('.')[:-1]) + '_' + suf + '.csv'
            self.generate_summary_headers(output_fn)
            cnt = 0
            num_of_records_for_avg = 0
            num_of_errors = 0
            wifi_scoring_link_data_gen = Tool.get_wifi_scoring_link_data_info(suf, cnt)
            wifi_scoring_air_data_gen = Tool.get_wifi_scoring_air_data_info(suf, cnt)
            wifi_monitoring_link_data_gen = Tool.get_wifi_monitoring_link_data_info(suf, cnt)
            wifi_monitoring_air_data_gen = Tool.get_wifi_monitoring_air_data_info(suf, cnt)
            flag = 0
            delta_total = 0.0
            while cnt < self.num_of_iter-1:
                time_info = str(self.period * cnt) + ','
                self.reset_temp_res_dict()
                try:
                    wifi_scoring_link_data_info, tx_link_effective_quality_score = next(wifi_scoring_link_data_gen)
                    wifi_scoring_air_data_info = next(wifi_scoring_air_data_gen)
                    wifi_monitoring_link_data_info, datarate = next(wifi_monitoring_link_data_gen)
                    wifi_monitoring_air_data_info = next(wifi_monitoring_air_data_gen)
                except FileNotFoundError as err:
                    self.utils.log(logging.ERROR, "An error occurred: " + err)
                    flag = 1
                if not wifi_scoring_link_data_info or not wifi_scoring_air_data_info or not wifi_monitoring_link_data_info or not wifi_monitoring_air_data_info:
                    break
                args_from_cmd = self.get_args_from_cmd()
                try:
                    actual_bitrate_loss_val = (float(self.dut_bitrate) - float(datarate)) / float(self.dut_bitrate) * 100.0
                    delta_val = float(tx_link_effective_quality_score) - actual_bitrate_loss_val
                    if abs(delta_val) <= self.tolerance: passed = ','
                    else: passed = 'Failed!,'
                    delta = str(delta_val) + ','
                    actual_bitrate_loss = str(actual_bitrate_loss_val) + ','
                except:
                    passed = delta = actual_bitrate_loss = 'N/A,'
                    num_of_errors += 1
                else:
                    if cnt > 1: # drop the first 2 results
                        num_of_records_for_avg += 1
                        delta_total += abs(delta_val)
                        self.accumulate_temp_results(actual_bitrate_loss_val)

                row_data = time_info + args_from_cmd + actual_bitrate_loss + delta + passed + wifi_scoring_link_data_info +\
                           wifi_scoring_air_data_info + wifi_monitoring_link_data_info + wifi_monitoring_air_data_info
                self.utils.write2file(output_fn, 'a', row_data)
                cnt += 1

            summary_data = self.prepare_avg_row(num_of_records_for_avg, delta_total)
            self.utils.write2file(output_fn, 'a', summary_data)
            if not flag: self.utils.log(logging.INFO, output_fn + ' was generated.')
            if num_of_errors > 0:
                self.utils.write2file(self.error_file, 'a', '{}: {} error(s) detected'.format(self.output_file, num_of_errors))


def main():
    parser = OptionParser()
    parser.add_option('--url', dest='url', type="string", default='https://192.168.1.1:8443',
                      help='URL address to collect data from, default: https://192.168.1.1:8443 (required)')
    parser.add_option('--dut-bitrate', dest='dut_bitrate', type='int', help='bit rate of device under test in Kbps (required)')
    parser.add_option('--external-ap-load', dest='external_ap_load', type='int', help='external AP load in Mbps (required)')
    parser.add_option('--external-ap-channel', dest='external_ap_channel', type='int', help='external AP channel (required)')
    parser.add_option('--period', dest='period', type="int", default=30, help='idletime between two samples, default: 30sec (optional)')
    parser.add_option('--tolerance', dest='tolerance', type="float", default=10.0, help='approved tolerance for bitrate loss in percents, default: 10.0% (optional)')
    parser.add_option('--duration', dest='duration', type="int", default=20*60, help='maximal duration of data collection process, default 1200sec (optional)')
    parser.add_option('--output', dest='output_file', type="string", default='output.csv', help='path to output file, default: output.csv (optional)')
    (opts, args) = parser.parse_args()
    assert opts.url is not None, "--url is required"
    assert opts.dut_bitrate is not None, "--dut-bitrate is required"
    assert opts.external_ap_load is not None, "--external-ap-load is required"
    assert opts.external_ap_channel is not None, "--external-ap-channel is required"
    assert 0.0 <= opts.tolerance <= 100.0, "--tolerance should be in the range [0, 100]"
    assert opts.duration > 0, "--duration should be positive integer"
    tool = Tool(url_val=opts.url, period_val=opts.period, output_file_val=opts.output_file,
                dut_bitrate=opts.dut_bitrate, external_ap_load=opts.external_ap_load,
                external_ap_channel=opts.external_ap_channel, tolerance=opts.tolerance,
                duration=opts.duration)
    utils.logger.log(logging.INFO, "Running with arguments:")
    utils.logger.log(logging.INFO, "--url {}".format(tool.url))
    utils.logger.log(logging.INFO, "--period {}".format(tool.period))
    utils.logger.log(logging.INFO, "--output {}".format(tool.output_file))
    utils.logger.log(logging.INFO, "--dut-bitrate {}".format(tool.dut_bitrate))
    utils.logger.log(logging.INFO, "--external-ap-load {}".format(tool.external_ap_load))
    utils.logger.log(logging.INFO, "--external-ap-channel {}".format(tool.external_ap_channel))
    utils.logger.log(logging.INFO, "--tolerance {}".format(tool.tolerance))
    utils.logger.log(logging.INFO, "--duration {}".format(tool.duration))
    utils.logger.log(logging.INFO, "\n(Ctrl+C to exit)\n")
    try:
        tool.run()
    except KeyboardInterrupt:
        tool.stop = datetime.datetime.now().time()
        tool.generate_summary()
        tool.exit_when_done()

    tool.stop = datetime.datetime.now().time()
    tool.generate_summary()
    tool.exit_when_done()

if __name__ == "__main__":
    main()
