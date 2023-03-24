# PostgreSQL database

## Construct the tables of database
They must be produced by pgmodeler tool with its own dbm format :
```
TVDatabase/TiledViz.dbm
```
and saved in the equivalent SQL file :
```
TVDatabase/TiledViz.sql
```


## postgres docker
We use the postgres:11.18-alpine docker to create the service with Gitlab-CI.
With TVSecure management, we construct a docker-swarm with a postgres service and use
secrets to give PostgreSQL password to Flask.
