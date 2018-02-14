#!/usr/bin/env python3

# global imports
from optparse import OptionParser
import os
import sys
import time
import glob
import logging
# local imports
import utils

SUMMARY_HEADER = ['scenario_id',
                  'actual bitrate loss [%]',             # calculated
                  'delta [%] (tx_link_effective_quality_score-actual bitrate loss)', # calculated
                  'test result',                         # calculated

                  'tx_link_effective_quality_score [%]', # /wifi_scoring/link_data
                  'tx_link_quality_score [%]',           # /wifi_scoring/link_data
                  'tx_retry_score [%]',                  # /wifi_scoring/link_data
                  'tx_phyrate_score [%]',                # /wifi_scoring/link_data
                  'channel_cca_user_impact [%]',         # /wifi_scoring/link_data

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


class SummaryGen(object):
    def __init__(self, dir_path, out_file):
        self.dir_path = dir_path
        self.out_file = out_file
        self.utils = utils.Utils()
        self.files_list = glob.glob(os.path.join(self.dir_path, '*.csv'))

    @classmethod
    def check_if_valid(cls, line):
        return True
        #return len(vec) == 25

    def process(self, fn):
        scenario_id = os.path.basename(fn)
        scenario_id = scenario_id[: scenario_id.find('.csv')]
        summary_vec = [scenario_id]
        last_line = open(fn, 'r').readlines()[-1]
        if not self.check_if_valid(last_line):
            return ''
        vec = [item for item in last_line.split(',') if len(item.strip()) > 0]
        for i in range(len(vec)):
            summary_vec.append(vec[i])
        return ','.join(summary_vec)

    def run(self):
        headers = ','.join(SUMMARY_HEADER)
        self.utils.write2file(self.out_file, 'w', headers)
        for f in self.files_list:
            summary_row = self.process(f)
            if len(summary_row) == 0:
                continue
            self.utils.write2file(self.out_file, 'a', summary_row)
            self.utils.log(logging.DEBUG, "{} processed".format(f))
        self.utils.log(logging.INFO, "{} created".format(self.out_file))


def main():
    parser = OptionParser()
    parser.add_option('--dir-path', dest='dir_path', type="string", help='path to the directory with .csv results (required)')
    parser.add_option('--output', dest='output', type="string", default='summary.csv', help='path to output file, default: summary.csv (optioanl)')
    (opts, args) = parser.parse_args()
    assert opts.dir_path is not None, "--dir-path is required"
    assert os.path.isdir(opts.dir_path), "{} is not directory or not exists".format(opts.dir_path)
    sumGen = SummaryGen(dir_path=opts.dir_path, out_file=opts.output)
    utils.logger.log(logging.INFO, "Running with arguments:")
    utils.logger.log(logging.INFO, "--dir-path {}".format(sumGen.dir_path))
    utils.logger.log(logging.INFO, "--output {}".format(sumGen.out_file))
    sumGen.run()

if __name__ == "__main__":
    main()
