# Postgresql server on localhost
* Default configuration : postgresql is only visible for localhost
```
sudo netstat -latupen |grep 5432
tcp        0      0 127.0.0.1:5432          0.0.0.0:* LISTEN      968        20388      2118/postgres
tcp6       0      0 ::1:5432                :::*      LISTEN      968        20387      2118/postgres     
```

# How to enable inside docker FlaskImage ?
1. Change inside /var/lib/pgsql
   * postgresql.conf :
`listen_addresses = 'localhost'	->  listen_addresses='*'`
   * pg_hba.conf :
`host    all             all             0.0.0.0/0         trust`

**It opens your postgresql service to the whole world !**

2. restart server:
`systemctl restart postgresql`
3. verify: 
```
sudo netstat -latupen |grep 5432
tcp        0      0 0.0.0.0:5432            0.0.0.0:* LISTEN      968        1556941    9599/postgres
tcp6       0      0 :::5432                 :::*      LISTEN      968        1556942    9599/postgres  
```

# Launch container with host (192.168.0.12 here) postgresql server :

```
export POSTGRES_HOST=postgres
export POSTGRES_DB=
export POSTGRES_PASSWORD=
export POSTGRES_USER=
docker run -it --name flaskdock --add-host="postgres:192.168.0.12" -p 5000 flaskimage  ${POSTGRES_HOST} ${POSTGRES_DB} ${POSTGRES_USER} ${POSTGRES_PASSWORD}
```
