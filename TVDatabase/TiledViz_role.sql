-- Database generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler  version: 0.9.0
-- PostgreSQL version: 9.6
-- Project Site: pgmodeler.com.br
-- Model Author: ---

-- object: tiledviz | type: ROLE --
-- DROP ROLE IF EXISTS tiledviz;
CREATE ROLE tiledviz WITH 
	SUPERUSER
	CREATEDB
	CREATEROLE
	INHERIT
	LOGIN
	ENCRYPTED PASSWORD 'm_test/@03';
-- ddl-end --

