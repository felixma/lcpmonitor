#!/usr/bin/env python

import os
import sys
import re
import pexpect,pxssh

def logon(server):
    #login = 'qima'
    #passwd = 'hello715'
    login = 'lss'
    passwd = 'lss'
    ssh = 'ssh -l %s %s' % (login, server)
    cmd = 'ls -l'

    with open('logonlcp.out', 'w') as f:
	child = pexpect.spawn(ssh)
        child.expect('Password: ')
        child.sendline(passwd)
        child.expect('day: ')
        child.sendline()
        child.expect('vi')
        child.sendline()
        child.expect('s00c0')
        #print child.after
        child.sendline(cmd)
	child.logfile_read = f
        #child.expect(pexpect.EOF)
        #print child.before
        child.expect('s00c0')
        child.sendline('exit')


if __name__ == '__main__':
    #logon('135.252.30.23')
    logon('135.252.130.66')

