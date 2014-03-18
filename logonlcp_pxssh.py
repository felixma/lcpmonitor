#!/usr/bin/env python

import os
import sys
import time
import re
import pexpect,pxssh

def logon(server):
    s = pxssh.pxssh()
    s.login(server, 'lss', 'lss')
#    s.sendline()
    #'''
    #s.expect('day: ')
    s.sendline('\n')
    #s.expect('vi')
    s.sendline('\n')
    #'''
    s.prompt()
    s.sendline('ls -l')
    print s.before
    s.logout()

if __name__ == '__main__':
    logon('135.252.130.66')

