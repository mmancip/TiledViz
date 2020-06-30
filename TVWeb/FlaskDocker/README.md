# Postgresql server on localhost
* Default configuration : postgresql is only visible for localhost
```
sudo netstat -latupen |grep 5432
tcp        0      0 127.0.0.1:5432          0.0.0.0:* LISTEN      968        20388      2118/postgres
tcp6       0      0 ::1:5432                :::*      LISTEN      968        20387      2118/postgres     
```

# How to enable inside docker FlaskImage ?
1. Get docker0 address
/sbin/ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+'

and to protect the DB and you must add docker0 address
(and note all network interfaces) in postgresql conf file (and '*' for all interfaces):
nano /var/lib/pgsql/data/postgresql.conf 
listen_addresses = 'localhost,172.17.0.1'
%    * pg_hba.conf :
% `host    all             all             0.0.0.0/0         trust`
% **It opens your postgresql service to the whole world !**

2. restart server:
`systemctl restart postgresql`
3. verify: 
```
sudo netstat -latupen |grep 5432
tcp        0      0 172.17.0.1:5432         0.0.0.0:*               LISTEN      980        1005010    28363/postgres      
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      980        1005009    28363/postgres      
tcp6       0      0 ::1:5432                :::*      LISTEN      980        1556942    9599/postgres  
```


# Launch container with host (192.168.0.12 here) postgresql server :

```
export POSTGRES_HOST=postgres
export POSTGRES_DB=
export POSTGRES_PASSWORD=
export POSTGRES_USER=
docker run -it --name flaskdock --add-host="postgres:192.168.0.12" -p 5000 flaskimage  ${POSTGRES_HOST} ${POSTGRES_DB} ${POSTGRES_USER} ${POSTGRES_PASSWORD}
```
