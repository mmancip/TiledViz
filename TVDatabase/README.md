Database is construted with pgmodeler

It is created with exported TiledViz.sql file.
psql  ...

model.py used by Flask and connections is built with : 
sqlacodegen postgres://user:password/host@db --outfile=TVmodels.py --flask

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
