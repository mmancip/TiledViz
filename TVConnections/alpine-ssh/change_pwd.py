#!env python

import sys
import pexpect

print("args : ",sys.argv[0],",",sys.argv[1],",",sys.argv[2])
user=sys.argv[1]
password=sys.argv[2]

child=pexpect.spawn("passwd "+user)
child.expect('Changing password for '+user)
child.expect('New password:')
child.sendline(password)
child.expect('Retype password:')
child.sendline(password)
child.sendline('passwd: password for '+user+'changed by root')
# passwd mmancip
# Changing password for mmancip
# New password:
# Retype password:
# passwd: password for mmancip changed by root
