Database is construted with pgmodeler

It is created with exported TiledViz.sql file.
psql  ...

model.py used by Flask and connections is built with : 
sqlacodegen postgres://user:password/host@db --outfile=TVmodels.py --flask

user:password are given in the start file of database constructor.
