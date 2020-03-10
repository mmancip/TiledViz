from __future__ import with_statement
import select
import sys,os,re,time
import threading
import datetime

import subprocess as subp

sys.path[0]=''
sys.path.append(os.path.abspath('/home/myuser/CASE'))
from connect import sock

PORT = 6501

SELECT_SEC=1

client=sock.client(PORT)

# sys.stdout.flush()
# search for last string of launch (wait 1s after each test)
Hostname=os.getenv("HOSTNAME")
LogFile="/home/myuser/.vnc/"+Hostname+".log"
OKLaunchStr="Log file is /home/myuser/.vnc/"+Hostname+":1.log"
StrPass='Random Password Generated: '

with open(LogFile) as LogFileDesc:
  for cnt, line in enumerate(LogFileDesc):
     if ( re.search(r''+StrPass,line) ):
        # Get vnc password in LogFile and send it to Connection
        p=re.compile(r''+StrPass+"(\w*)")
        PasswdStr=p.sub(r'\1',line.rstrip())
        print("Passwd =",PasswdStr)
        sys.stdout.flush()
        PasswdMSG=sys.argv[1]+":"+PasswdStr
        client.send_server(PasswdMSG)

        CommandIp="/sbin/ip addr show dev eth0"
        p=subp.Popen(CommandIp, shell=True,stdout=subp.PIPE,stderr=subp.PIPE)
        output, errors = p.communicate()
        output.decode('utf-8')
        OutIp=re.sub(r'.*inet ([^/]*)/24 .*',r'\1',output.replace('\n',''))

     elif ( re.search(r''+OKLaunchStr,line.rstrip()) ):
        # Get OKLaunchStr in LogFile
        print("Find end of startup.")
        sys.stdout.flush()

#=> communication to server
print("Wait for commands.")
sys.stdout.flush()

while True:
    data = client.recv()
    if not data: break
    CommandRecv=data
    print("Receive data : "+CommandRecv)
    if (re.search(r'execute',CommandRecv)):
        CommandData=CommandRecv.replace("execute ","")
        print("Execute command : "+CommandData)
        #Log outputs of commands : 
        # fsocat.append(open("pid_dist","w"))
        # socatSERV.append(subp.Popen( (strsocat.split(' ')), stdout=fsocat[i]))
        # time.sleep(2)
        # fsocat[i].flush()
        
        # f3141=open("pid_dist","r")
        # pidsocat.append(f3141.readline().replace('\n',''))
        # f3141.close()
        # print "socat : ",strsocat,pidsocat[i]

        try:
            #DATE=re.sub(r'\..*','',datetime.datetime.isoformat(datetime.datetime.now(),sep='_').replace(":","-"))
            #process=subp.Popen( CommandData, shell=True, stdout=subp.PIPE,stderr=subp.PIPE ) 
            # output, errors = process.communicate()
            # print(output.decode('utf-8'))
            # if (len(errors) >0):
            #     print(errors.decode('utf-8'))
            #outprocess=process.returncode

            process=os.system( CommandData )
            outprocess=os.WEXITSTATUS(process)
            print("outprocess = "+str(outprocess))

            client.send_OK(outprocess)

        except Exception as err:
            print("Error on execution : "+str(err))
            client.send_OK(-1)
    else:
        print("Get unknown command : "+CommandRecv)

client.close()
