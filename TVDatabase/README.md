Database is constructed with pgmodeler

To initialize the postgres DB on localhost, you must
use root account and change to postgres and create tiledviz role :
{{{
[myyser@localhost] su -
[root@localhost]# su - postgres
[postgres@localhost ~]$ createuser -h localhost -d tiledviz
}}}
Finnaly you have to create the TiledViz DB with you account :
{{{
[myyser@localhost] createdb -h localhost -U tiledviz TiledViz
}}}

It is created with exported TiledViz.sql file. Example in TVDatabase/filledDatabase.sh
{{{
psql -h "${POSTGRES_HOST}" -U "$POSTGRES_USER" -d "$POSTGRES_DB"  -f TVDatabase/TiledViz.sql
}}}

model.py used by Flask and connections is built with : 
sqlacodegen postgres://user:password/host@db --outfile=models.py --flask

user:password are given in the start file of database constructor.


Management functions on the database :
definitions in management.sql
Add with
{{{
psql -h localhost -U tiledviz -d TiledViz -f TVDatabase/management.sql
}}}
View unused tilesets with :
VIEW FreeTileSets

TODO : build unused view for empty sessions and delete unused sessions.
VIEW EmptySessions

TODO : add admin column for user table, build flask management pages.
