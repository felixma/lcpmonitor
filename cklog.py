#!/usr/bin/env python

import os
import sys
#sys.path.append('/home/felix/python')
import time
import re
import pexpect,pxssh
import mail

LAB = { 
	'qd02' : '10.87.9.9',
	'qd03' : '10.87.9.41',
	'qd04' : '10.87.9.73',     # qd04 CNFG
#	'qd05' : '10.87.9.89',
#	'qd06' : '135.252.138.66',
#	'ibc01' : '10.87.9.165',
	'scg01' : '10.87.9.102'
      }

HOME = '/home/felix/python/lcp/log/'
master_log = '/export/home/lss/logs/master.log'
log_dir_on_lcp = '/storage/CheckLog/'
ERROR = []
QUIET_LOG_LENGTH = 115 ## when no error in lab.log, the length of lab.log is 112 for qd03.log and 113 for scg01.log
QUIET = True

def cklog(server):
    '''
    This function will do:
    1. Search(grep) Assert and SegV in master.log
       The grep output will be saved to /home/felix/python/lcp/log/{lab}.log on qdnlt server, e.g. qd04.log
    2. If find, copy master.log to /storage/CheckLog/ on lsp host with a timestamp, e.g. master.log.20130719131911
       The timestamp will be written in /home/felix/python/lcp/log/{lab}.timestamp, e.g. qd04.timestamp
    '''

    global QUIET
    QUIET = True

    login = 'lss'
    passwd = 'lss'
    #passwd = 'lss\n'  ## \n is required by pexpect.run()
    #master_log = '/storage/felix/AssertSeg.log'
    #master_log = '/export/home/lss/logs/master.log'
    #log_dir_on_lcp = '/storage/CheckLog/'
    logtag = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))

    ssh_cmd = 'ssh -l %s %s' % (login, LAB[server])
    #install_sshkey_cmd = 'ssh-copy-id %s@%s\n' % (login, LAB[server])   ## \n is required by pexpect.run()
    ck_error_cmd = 'grep -A 10 -B 2 -E "Assert:|Report 1" %s' % master_log
    create_logdir_on_lcp_cmd =  'mkdir -p %s' % log_dir_on_lcp
    cp_errorlog_cmd = 'cp %s %smaster.log.%s' % (master_log, log_dir_on_lcp, logtag)   ## master.log is saved as 'master.log.20130717223647'

    print 'Going to check %s...' % server

    #with open('/home/felix/python/lcp/log/%s.log' % server, 'w') as f:
    with open('%s%s.log' % (HOME, server), 'w+') as f:
    #child = pexpect.spawn(ssh, maxread = 50000)
	    
   ###try:
	###child = pexpect.run(install_sshkey_cmd, events = {'Password:': passwd})
	###print 'install ssh key on %s successfully.' % server
	###child.expect('Password:')
	###child.sendline(passwd)
   ###except pexpect.TIMEOUT:
	###print "Fail to install ssh key to %s" % server

        child = pexpect.spawn(ssh_cmd)
        #child.logfile = sys.stdout
        #child.maxread = 500000
        #child.logfile = sys.stdout
        try:
  	    child.expect('Password: ')
	    child.sendline(passwd)   ### password isn't needed if ssh key is installed
	    child.expect('day: ')
	    #child.sendline('\r')
	    child.sendline()
	    child.expect('vt220')
	    child.sendline()
	    child.expect('vi')
	    child.sendline()
	    child.expect('s00c0')
	    #child.expect('/export/home/lss')
	    child.sendline(ck_error_cmd)
	    child.logfile_read = f
	    #child.logfile_read = sys.stdout
	    #child.expect(pexpect.EOF)
	    
	    #f.seek(0)  ## not work, should behind of the next expect....
	    child.expect('s00c0')  ## It's interesting: if expect('/export/home/lss'), no output can be saved to logfile except the sent command!!!! Because '/export/home/lss' is a part of the sent command!!! pexpect thinks it has already match it when sending the command
	    #child.expect('/export/home/lss')
	    #child.logfile_send = sys.stdout

	    f.seek(0)   ### this is important!!
	    #print 'position: %d' % f.tell()
	    #print f.read()
	    #haha = len(f.read())
	    #print haha
	    #f.seek(0)
	    #print f.read()
	    loglength = len(f.read())
	    #if len(f.read()) > QUIET_LOG_LENGTH:
	    if loglength > QUIET_LOG_LENGTH:
		QUIET = False
		#print 'loglength: %d' % loglength
	        print 'going to copy master.log'
	        child.sendline(create_logdir_on_lcp_cmd + '|' + cp_errorlog_cmd)
                with open('%s%s.timestamp' % (HOME, server), 'w') as timestamp:
		    timestamp.write(logtag)
            else:
		print 'loglength: %d' % loglength
	        #print 'not to save master.log'
	        child.sendline()
	    child.logfile_read = None
            child.expect('s00c0')
	    #child.logfile_read = None   ### disable logging not work
            child.sendline('exit')
	    #print 'Quiting cklog()...'
	except pexpect.TIMEOUT, e:
	    print "can't log on %s to run %s" % (server, ck_error_cmd)
	    print e


def parselog(server):
    '''
    This function will parse log under /home/felix/python/lcp/log/ if there is Assert or SegV.
    It calls getfbt() to get function back trace.
    1. Write Assert name and function back trace in /home/felix/python/lcp/log/{lab}.fbt, e.g. qd04.fbt 
    2. Write SegV Report 0 and function back trace in /home/felix/python/lcp/log/{lab}.fbt 
    3. Add "ASSERT" or "SegV" in the global list ERROR
    4. For Assert, make a summary(name, timestamp) in /home/felix/python/lcp/log/{lab}.astsummary, e.g. qd04.astsummary
    '''
    print 'going through parselog()...'
    global QUIET
    if QUIET == True:
        print '%s is quiet, quiting parselog()...' % server
    else:
        with open('%s%s.log' % (HOME, server), 'r') as grepout:
	    #if len(grepout.read()) == 0:
	    hascontent = len(grepout.read())
	    if hascontent == 0:
	        print "didn't get info on %s!\n" % server
	    elif 0 < hascontent < QUIET_LOG_LENGTH:
	        print '%s is quiet\n' % server
	    else:
	        QUIET = False
	        grepout.seek(0)  ### go back to the beginning of file
	        print 'start to parse %s log\n' % server
	        with open('%s%s.fbt' % (HOME, server), 'w') as fbtout, open('%s%s.astsummary' % (HOME, server),'w+') as astsummary:
		    all_in_one_string = grepout.read()
		    splitted_into_list = re.split('--', all_in_one_string)
		    #print splitted_into_list

		    reg_app = r'ngss|fs5000|h248ds|aim|fchk|feph'
		    reg_assert_trace = r'Function Trace:\s+(([0-9a-f]{8}\s+)+)'   ### there is one more \r than it is on lcp host
		    reg_segv_trace = r'Function trace \(from signal context\):\s+(([0-9a-f]{8}\s+)+)'    ### () means subgroup in RE, so have to use \( and \)
		    reg_assert_timestamp = r'(\d{4}/\d\d/\d\d\s+\d\d:\d\d:\d\d\.\d\d\d)\sASSERT'
		    #reg_assert_name = r'Assert: ([A-Za-z_]\s?)+\(\)'  ## NOK
		    #reg_assert_name = r'Assert: (\w\s?)+\(\)'   ## NOK
		    #reg_assert_name = r'Assert: (\w(\s)*(\.)*)+\(\)' ##OK
		    reg_assert_name = r'Assert: ([\w\s\.]*)+\(\)'
		    ast = {}

		    for each_error in splitted_into_list:
		        #fbtout.write(each_error)
		    
		        ### get ASSERT name, timestamp ###
		        astname = re.search(reg_assert_name, each_error)
		        asttime = re.search(reg_assert_timestamp, each_error)
		        if astname is not None and asttime is not None:
			    #ast[m.group()] = n.group()
			    print 'astname: %s' % astname.group()
			    print 'asttime: %s' % asttime.group(1)
			    astsummary.write('\t'.join([astname.group(), asttime.group(1), '\n']))
		        else:
			    print 'no need to add into Assert summary!\n'
			    #print each_error
			    print '\n'
		    
		        ### find application ###
		        app = re.search(reg_app, each_error)
		        if app is not None:
			    application = app.group()
			    #print application
		        else:
			    continue

		        #reg_assert = r'Function Trace:\s(([0-9a-f]{8}\s)+)'
		        #reg_assert_trace = r'Function Trace:\s+(([0-9a-f]{8}\s+)+)'   ### there is one more \r than it is on lcp host
		        asttrace = re.search(reg_assert_trace, each_error)
		        if asttrace is not None:
			    #assert_fbt = m.group(1).replace('\n', ' ')
			    assert_fbt = asttrace.group(1).replace('\n', ' ').replace('\r', ' ')
			    #print assert_fbt
			    #print getfbt(server, application, assert_fbt)
			    fbtout.write(astname.group())
			    fbtout.write(getfbt(server, application, assert_fbt))
			    fbtout.write('-----\n\n')
			    if 'ASSERT' not in ERROR:
			        ERROR.append('ASSERT')
		        #else:
			    #print 'not match. Error is %s' % each_error
		    
		        #reg_segv_trace = r'Function trace \(from signal context\):\s+(([0-9a-f]{8}\s+)+)'    ### () means subgroup in RE, so have to use \( and \)
		        segvtrace = re.search(reg_segv_trace, each_error)
		        if segvtrace is not None:
			    segv_fbt = segvtrace.group(1).replace('\n', ' ').replace('\r', ' ')
			    fbtout.write(each_error)
			    fbtout.write(getfbt(server, application, segv_fbt))
			    fbtout.write('-----\n\n')
			    if 'SegV' not in ERROR:
			        ERROR.append('SegV')



    """ 
   def getfbt(server, app, fbt):
    print 'fbt is %s' % fbt
    login = 'lss'
    passwd = 'lss'
    ssh_cmd = 'ssh -l %s %s' % (login, LAB[server])
    cmd = '/export/home/lss/bin/lcp_trace linux_x86 /export/home/lss/logreader/linux_x86/%s.elf %s' % (app, fbt)
    
    #s = pxssh.pxssh()
    #s.login(server, 'lss', 'lss')
    #s.sendline()
    #s.expect('day: ')
    #s.sendline()
    #s.expect('vi')
    #s.sendline()
    #s.prompt()
    #s.sendline(cmd)
    #fbttrace = s.before
    #print fbttrace
    #s.logout()
    
    with open('%s.fbt' % server, 'w+') as f:
	child = pexpect.spawn(ssh_cmd)
        child.expect('Password: ')
        child.sendline(passwd)
        child.expect('day: ')
        child.sendline()
	child.expect(r'vi): ')
        child.sendline()
        child.expect('s00c0')
        child.sendline(cmd)
	child.logfile_read = f
        child.expect('s00c0')
        child.sendline('exit')
	#child.logfile = None
	f.seek(0)      #### This is important!!! Because child.logfile_read = f will rush the content to f and the pointer goes to EOF
	return f.read() 
    """

def getfbt(server, app, fbt):
    '''
    This function calls lcp_trac to get function back trace details.
    Note: pexpect.run(cmd...) can return a string containing the output of cmd.
    See details: http://pexpect.sourceforge.net/pexpect.html
    '''
    #print 'going through getfbt()...'
    print 'fbt is %s' % fbt
    login = 'lss'
    passwd = 'lss\n'
    ssh_cmd = 'ssh -l %s %s' % (login, LAB[server])
    try:
        gettrace_cmd = '/export/home/lss/bin/lcp_trace linux_x86 /export/home/lss/logreader/linux_x86/%s.elf %s\n' % (app, fbt)
    #cmd = ' '.join([ssh_cmd, gettrace_cmd])
    #print cmd

    #return pexpect.run(' '.join([ssh_cmd, gettrace_cmd]), events={'Password: ': passwd, 'day: ': '\n', 'vi': '\n'})
    ###str.split('Password:') - if not split, additional string will be returned:
    ###Unauthorized use of this system is prohibited and may be prosecuted
    ###to the fullest extent of the law. By using this system, you implicitly
    ###agree to monitoring by system management and law enforcement authorities.
    ###If you do not agree with these terms, DISCONNECT NOW.
    ###
    ###Password:
        return pexpect.run(' '.join([ssh_cmd, gettrace_cmd]), events={'Password: ': passwd}).split('Password:')[1]#, 'day: ': '\n', 'vi': '\n'})
    except pexpect.TIMEOUT, e:
        print 'get fbt failed:\n'
        print e
    #fbt= pexpect.run(cmd, events={'Password: ': passwd})#, 'day: ': '\n', 'vi': '\n'})
    #return fbt.rpartition('Password:')[2]  ## it's OK too
    #return fbt.split('Password:')[1]

def notify(server):
    '''
    This function calls send_mail() in mails module to notify team if there is errors in master.log
    '''
    print 'going through notify()...'
    global QUIET
    if QUIET == True:
	print '%s is quiet, quiting notify()...\n' % server
    else:
	print 'QUIET is %s' % QUIET
    	smtp_server = '135.5.2.65'
        fro = "felix.ma@alcatel-lucent.com"
        #to  = ["felix.ma@alcatel-lucent.com"]
        to  = ["qd-ims-mtce-nlt@LIST.ALCATEL-LUCENT.COM"]
         
        labprefix    = ''.join([HOME, server])
        timestamplog = ''.join([labprefix, '.timestamp'])
        labmail      = ''.join([labprefix, '.mail'])
        astsummary   = ''.join([labprefix, '.astsummary'])
        fbtdetails   = ''.join([labprefix, '.fbt'])
        grepout      = ''.join([labprefix, '.log'])
        grepoutold   = ''.join([grepout, '.old'])

        sendflag = 0
    
        if not os.path.exists(timestamplog):
	    print 'no error, not send email'
	    sendflag = 0
        else:
	    if not os.path.exists(grepoutold):
	        print 'has error and no old log, so sending email...'
	        sendflag = 1
	        os.rename(grepout, grepoutold)
            else:
	        print 'comparing old error and new error...'
	        #os.remove(timestamplog)
	        with open(grepout) as f1, open(grepoutold) as f2:
	            if f1.read().split('CheckLog')[0] == f2.read().split('CheckLog')[0]:
		        print 'log has no new error than old log, not send email.'
		        sendflag = 0
		        os.rename(grepout, grepoutold)
		        #os.remove(timestamplog)
	            else:
		        print 'log has new error than old log, sending email...'
		        sendflag = 1
		        os.rename(grepout, grepoutold)
    
        if sendflag == 1:
	    err = '/'.join(ERROR)
	    subject = '%s fires in %s master.log' % (err, server)
	    with open(timestamplog) as ts, open(labmail, 'w+') as content:
	        content.write('master.log is saved on %s: %smaster.log.%s\n' % (server, log_dir_on_lcp, ts.read()))
	        content.write('----------\n')
	        if 'ASSERT' in ERROR:
		    with open(astsummary) as astsum:
		        content.write('ASSERT summary:\n\n')
		        content.write(astsum.read())
	        with open(fbtdetails) as fbt:
		    content.write(fbt.read())
	        content.seek(0)   ### important! otherwise no email body!!!
	        mail.send_mail(smtp_server, fro, to, subject, content.read())

	if os.path.exists(timestamplog):
	    os.remove(timestamplog)


def main():
    #qd04 = '135.252.130.66'
	
    for lab in LAB.keys():
    	#print lab
	cklog(lab)
	parselog(lab)
	notify(lab)
    #cklog('qd04')
    #parselog('qd04')
    #notify('qd04')

if __name__ == '__main__':
    main()
