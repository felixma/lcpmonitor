#!/usr/bin/env python

'''
mlogparser checks ASSERT/SegV/AUDIT in master.log on LCP host.
For ASSERT and SegV, it calls lcp_trace to get Function Back Trace.
The output is saved under /storage/felix/CheckLog/LOG/
'''

import re
import os
import time


def checklog():
    #MASTERLOG = '/export/home/lss/logs/master.log'
    MASTERLOG = '/storage/felix/AssertSeg.log'
    ERROR = 'Assert:|Segmentation Violation|AUDIT'
    HOMEDIR = '/storage/felix/CheckLog/LOG/'
    LCPTRACE = '/export/home/lss/bin/lcp_trace'
    
    #os.system('grep -A 20 -B 2 -E "Assert:|Report 1" %s > %s+".out"' % (MASTERLOG, HOMEDIR))
    if os.system('grep -A 20 -B 2 -E "Assert:|Report 1" %s > grepout.log"' % MASTERLOG):
        with open('grepout.log') as grepout,open('output.log', 'w') as output:
            all_in_one_string = grepout.read()
            splitted_into_list = re.split('--', all_in_one_string)  ### The grep cmd has a separator '--'. ###
            for each_error in splitted_into_list:
                output.write(each_error)
                
                '''
                parser error 
                '''
                reg_app = r'ngss|fs5000|h248ds|aim|fchk|feph'
                m = re.search(reg_app, each_error)
                if m is not None: application = m.group()

                #'Function Trace:\n(regular)\n\nRegister Dump' or 'Function trace (from signal context):\n(regular)\n\r\n+++'

                #'Function Trace:\n([0-9a-f ]{8}+)\n\nRegister Dump' or 'Function trace (from signal context):\n([0-9a-f ]{8}+)\n\r\n+++'

                #reg_assert = r'Function Trace:\n(([0-9a-f]{8}\s)+)\n\nRegister Dump'
                reg_assert = r'Function Trace:\n(([0-9a-f]{8}\s)+)'           ### \s matches any blank character, equals to [\n\r\t\v\f]
                m = re.search(reg_assert, each_error)
                if m is not None: 
                    assert_fbt = m.group(1).replace('\n', ' ')
                    assert_fbt_out = os.system('/export/home/lss/bin/lcp_trace linux_x86 /export/home/lss/logreader/linux_x86/%s.elf %s' %(application, assert_fbt))
                    output.write(assert_fbt_out)

                reg_segv = r'Function trace \(from signal context\):\s(([0-9a-f]{8}\s)+)'    ### () means subgroup in RE, so have to use \( and \)
                m = re.search(reg_segv, each_error)
                if m is not None: 
                    segv_fbt = m.group(1).replace('\n', ' ')
                    segv_fbt_out = os.system('/export/home/lss/bin/lcp_trace linux_x86 /export/home/lss/logreader/linux_x86/%s.elf %s' %(application, assert_fbt))
                    output.write(assert_fbt_out)

                ## try to merge the two regular expressions into one!
                #reg = r'Function trace \(from signal context\):\s(([0-9a-f]{8}\s)+)|Function Trace:\n(([0-9a-f]{8}\s)+)'

def main():
    checklog()

if __name__ == '__main__':
    main()
