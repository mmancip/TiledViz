#!/usr/bin/python3
import pexpect, re, sys

cmdgen="openssl req -new -x509 -days 1 -nodes -out self.pem -keyout self.pem"

childgen=pexpect.spawnu(cmdgen) #, logfile=sys.stdout.buffer)
childgen.logfile=sys.stdout
#childgen.setecho(True)
#expindex=childgen.expect('Generating a RSA private key')

#expindex=childgen.expect(r".*Country Name \(2 letter code\) \[.*\]:")
#if (expindex == 0):
    
outpass = childgen.sendline(r'FR')

#expindex=childgen.expect('State or Province Name (full name) [Some-State]:')
#if (expindex == 0):
    
outpass = childgen.sendline(r'France')
    
#expindex=childgen.expect('Locality Name (eg, city) []:')
#if (expindex == 0):
    
outpass = childgen.sendline(r'Paris')
    
#expindex=childgen.expect('Organization Name (eg, company) [Internet Widgits Pty Ltd]:')
#if (expindex == 0):
    
outpass = childgen.sendline(r'CNRS')

#expindex=childgen.expect('Organizational Unit Name (eg, section) []:')
#if (expindex == 0):
    
outpass = childgen.sendline(r'MDLS')
#child.send ('\x20')
#expindex=childgen.expect('Common Name (e.g. server FQDN or YOUR name) []:')
#if (expindex == 0):
    
outpass = childgen.sendline(r'Mancip')

#expindex=childgen.expect('Email Address []:')
#if (expindex == 0):
    
outpass = childgen.sendline(r'Martial.Mancip@MaisondelaSimulation.fr')
    
try:
    childgen.expect(pexpect.EOF)
except:
    pass
childgen.close(force=True)

