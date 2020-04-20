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


-- Database creation must be done outside an multicommand file.
-- These commands were put in this file only for convenience.
-- -- object: "TiledViz" | type: DATABASE --
-- -- DROP DATABASE IF EXISTS "TiledViz";
-- CREATE DATABASE "TiledViz"
-- 	TEMPLATE = template0
-- 	ENCODING = 'UTF8'
-- 	LC_COLLATE = 'en_US.utf-8'
-- 	LC_CTYPE = 'en_US.utf-8'
-- 	TABLESPACE = pg_default
-- 	OWNER = tiledviz
-- ;
-- -- ddl-end --
-- 

-- object: public.projects_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS public.projects_id_seq CASCADE;
CREATE SEQUENCE public.projects_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
ALTER SEQUENCE public.projects_id_seq OWNER TO tiledviz;
-- ddl-end --

-- object: public.users_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS public.users_id_seq CASCADE;
CREATE SEQUENCE public.users_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
ALTER SEQUENCE public.users_id_seq OWNER TO tiledviz;
-- ddl-end --

-- object: public.users | type: TABLE --
-- DROP TABLE IF EXISTS public.users CASCADE;
CREATE TABLE public.users(
	id integer NOT NULL DEFAULT nextval('public.users_id_seq'::regclass),
	name character varying(80) NOT NULL,
	creation_date timestamp,
	mail character varying(80),
	compagny character varying,
	manager character varying(80),
	salt character(20) NOT NULL,
	password character(128),
	dateverified timestamp,
	CONSTRAINT users_pkey PRIMARY KEY (id),
	CONSTRAINT uniq_users UNIQUE (name)

);
-- ddl-end --
COMMENT ON COLUMN public.users.manager IS 'Project manager';
-- ddl-end --
ALTER TABLE public.users OWNER TO tiledviz;
-- ddl-end --

-- object: public.projects | type: TABLE --
-- DROP TABLE IF EXISTS public.projects CASCADE;
CREATE TABLE public.projects(
	id integer NOT NULL DEFAULT nextval('public.projects_id_seq'::regclass),
	id_users integer,
	name character varying(80) NOT NULL,
	creation_date timestamp,
	description character varying(120),
	CONSTRAINT projects_pkey PRIMARY KEY (id),
	CONSTRAINT uniq_project UNIQUE (name)

);
-- ddl-end --
ALTER TABLE public.projects OWNER TO tiledviz;
-- ddl-end --

-- object: public.invite_links_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS public.invite_links_id_seq CASCADE;
CREATE SEQUENCE public.invite_links_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
ALTER SEQUENCE public.invite_links_id_seq OWNER TO tiledviz;
-- ddl-end --

-- object: public.invite_links | type: TABLE --
-- DROP TABLE IF EXISTS public.invite_links CASCADE;
CREATE TABLE public.invite_links(
	id integer NOT NULL DEFAULT nextval('public.invite_links_id_seq'::regclass),
	link character varying(200) NOT NULL,
	host_user character varying(80) NOT NULL,
	host_project character varying(80) NOT NULL,
	type boolean,
	creation_date timestamp,
	id_sessions integer,
	id_users integer,
	CONSTRAINT invite_links_pkey PRIMARY KEY (id),
	CONSTRAINT invite_links_link_key UNIQUE (link)

);
-- ddl-end --
ALTER TABLE public.invite_links OWNER TO tiledviz;
-- ddl-end --

-- object: public.sessions_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS public.sessions_id_seq CASCADE;
CREATE SEQUENCE public.sessions_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
ALTER SEQUENCE public.sessions_id_seq OWNER TO tiledviz;
-- ddl-end --

-- object: public.sessions | type: TABLE --
-- DROP TABLE IF EXISTS public.sessions CASCADE;
CREATE TABLE public.sessions(
	id integer NOT NULL DEFAULT nextval('public.sessions_id_seq'::regclass),
	name character varying(80) NOT NULL,
	id_projects integer NOT NULL,
	creation_date timestamp,
	description character varying(120),
	"Number_of_active_users" smallint,
	timeout integer,
	config json,
	CONSTRAINT sessions_pkey PRIMARY KEY (id),
	CONSTRAINT uniq_session UNIQUE (name)

);
-- ddl-end --
COMMENT ON COLUMN public.sessions."Number_of_active_users" IS 'Number of users actively connected to this sessions';
-- ddl-end --
COMMENT ON COLUMN public.sessions.timeout IS 'Set the timeout (in seconds) after which a session is disactivated (Number_of_active_users is 0) while no socket is still connected.';
-- ddl-end --
COMMENT ON COLUMN public.sessions.config IS 'configuration of the grid for this session';
-- ddl-end --
ALTER TABLE public.sessions OWNER TO tiledviz;
-- ddl-end --

-- object: public.connections_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS public.connections_id_seq CASCADE;
CREATE SEQUENCE public.connections_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
ALTER SEQUENCE public.connections_id_seq OWNER TO tiledviz;
-- ddl-end --

-- object: public.connections | type: TABLE --
-- DROP TABLE IF EXISTS public.connections CASCADE;
CREATE TABLE public.connections(
	id integer NOT NULL DEFAULT nextval('public.connections_id_seq'::regclass),
	creation_date timestamp,
	host_address character varying(40),
	auth_type character varying(10),
	container character varying(100),
	id_users integer NOT NULL,
	scheduler character varying(15),
	scheduler_file character varying(30),
	config_files json,
	CONSTRAINT connections_pkey PRIMARY KEY (id)

);
-- ddl-end --
ALTER TABLE public.connections OWNER TO tiledviz;
-- ddl-end --

-- object: public.tiles_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS public.tiles_id_seq CASCADE;
CREATE SEQUENCE public.tiles_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
ALTER SEQUENCE public.tiles_id_seq OWNER TO tiledviz;
-- ddl-end --

-- object: public.tiles | type: TABLE --
-- DROP TABLE IF EXISTS public.tiles CASCADE;
CREATE TABLE public.tiles(
	id integer NOT NULL DEFAULT nextval('public.tiles_id_seq'::regclass),
	title character varying(80),
	pos_px_x integer NOT NULL,
	pos_px_y integer NOT NULL,
	pos_id_x integer,
	pos_id_y integer,
	comment text,
	source json NOT NULL,
	tags json,
	id_connections integer,
	creation_date timestamp,
	"IdLocation" smallint,
	CONSTRAINT tiles_pkey PRIMARY KEY (id)

);
-- ddl-end --
COMMENT ON COLUMN public.tiles.source IS 'source of the tile : may be an url or a path in a directory of initial conditions or a list of paths.';
-- ddl-end --
ALTER TABLE public.tiles OWNER TO tiledviz;
-- ddl-end --

-- object: public.tile_sets_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS public.tile_sets_id_seq CASCADE;
CREATE SEQUENCE public.tile_sets_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
ALTER SEQUENCE public.tile_sets_id_seq OWNER TO tiledviz;
-- ddl-end --

-- object: public.tile_sets | type: TABLE --
-- DROP TABLE IF EXISTS public.tile_sets CASCADE;
CREATE TABLE public.tile_sets(
	id integer NOT NULL DEFAULT nextval('public.tile_sets_id_seq'::regclass),
	name character varying(80) NOT NULL,
	type_of_tiles character varying(15) NOT NULL,
	"Dataset_path" character varying(100),
	id_connections integer,
	creation_date timestamp,
	source json,
	config_files json,
	launch_file character varying(30),
	CONSTRAINT tile_sets_pkey PRIMARY KEY (id)

);
-- ddl-end --
COMMENT ON COLUMN public.tile_sets.type_of_tiles IS 'must discribe the nature sources of the tiles connected for this tile_set. In this list : web png, local image, remote database file, set of database remote files';
-- ddl-end --
COMMENT ON COLUMN public.tile_sets."Dataset_path" IS 'Path of  the database for this tile_set.';
-- ddl-end --
ALTER TABLE public.tile_sets OWNER TO tiledviz;
-- ddl-end --

-- object: public.sockets_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS public.sockets_id_seq CASCADE;
CREATE SEQUENCE public.sockets_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
ALTER SEQUENCE public.sockets_id_seq OWNER TO tiledviz;
-- ddl-end --

-- object: public.many_users_has_many_sessions | type: TABLE --
-- DROP TABLE IF EXISTS public.many_users_has_many_sessions CASCADE;
CREATE TABLE public.many_users_has_many_sessions(

);
-- ddl-end --

-- object: id_users | type: COLUMN --
-- ALTER TABLE public.many_users_has_many_sessions DROP COLUMN IF EXISTS id_users CASCADE;
ALTER TABLE public.many_users_has_many_sessions ADD COLUMN id_users integer NOT NULL;
-- ddl-end --


-- object: id_sessions | type: COLUMN --
-- ALTER TABLE public.many_users_has_many_sessions DROP COLUMN IF EXISTS id_sessions CASCADE;
ALTER TABLE public.many_users_has_many_sessions ADD COLUMN id_sessions integer NOT NULL;
-- ddl-end --

-- object: many_users_has_many_sessions_pk | type: CONSTRAINT --
-- ALTER TABLE public.many_users_has_many_sessions DROP CONSTRAINT IF EXISTS many_users_has_many_sessions_pk CASCADE;
ALTER TABLE public.many_users_has_many_sessions ADD CONSTRAINT many_users_has_many_sessions_pk PRIMARY KEY (id_users,id_sessions);
-- ddl-end --


-- object: users_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_users_has_many_sessions DROP CONSTRAINT IF EXISTS users_fk CASCADE;
ALTER TABLE public.many_users_has_many_sessions ADD CONSTRAINT users_fk FOREIGN KEY (id_users)
REFERENCES public.users (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: sessions_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_users_has_many_sessions DROP CONSTRAINT IF EXISTS sessions_fk CASCADE;
ALTER TABLE public.many_users_has_many_sessions ADD CONSTRAINT sessions_fk FOREIGN KEY (id_sessions)
REFERENCES public.sessions (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: projects_fk | type: CONSTRAINT --
-- ALTER TABLE public.sessions DROP CONSTRAINT IF EXISTS projects_fk CASCADE;
ALTER TABLE public.sessions ADD CONSTRAINT projects_fk FOREIGN KEY (id_projects)
REFERENCES public.projects (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: public.many_tiles_has_many_tile_sets | type: TABLE --
-- DROP TABLE IF EXISTS public.many_tiles_has_many_tile_sets CASCADE;
CREATE TABLE public.many_tiles_has_many_tile_sets(

);
-- ddl-end --

-- object: id_tiles | type: COLUMN --
-- ALTER TABLE public.many_tiles_has_many_tile_sets DROP COLUMN IF EXISTS id_tiles CASCADE;
ALTER TABLE public.many_tiles_has_many_tile_sets ADD COLUMN id_tiles integer NOT NULL;
-- ddl-end --


-- object: id_tile_sets | type: COLUMN --
-- ALTER TABLE public.many_tiles_has_many_tile_sets DROP COLUMN IF EXISTS id_tile_sets CASCADE;
ALTER TABLE public.many_tiles_has_many_tile_sets ADD COLUMN id_tile_sets integer NOT NULL;
-- ddl-end --

-- object: many_tiles_has_many_tile_sets_pk | type: CONSTRAINT --
-- ALTER TABLE public.many_tiles_has_many_tile_sets DROP CONSTRAINT IF EXISTS many_tiles_has_many_tile_sets_pk CASCADE;
ALTER TABLE public.many_tiles_has_many_tile_sets ADD CONSTRAINT many_tiles_has_many_tile_sets_pk PRIMARY KEY (id_tiles,id_tile_sets);
-- ddl-end --


-- object: tiles_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_tiles_has_many_tile_sets DROP CONSTRAINT IF EXISTS tiles_fk CASCADE;
ALTER TABLE public.many_tiles_has_many_tile_sets ADD CONSTRAINT tiles_fk FOREIGN KEY (id_tiles)
REFERENCES public.tiles (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: tile_sets_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_tiles_has_many_tile_sets DROP CONSTRAINT IF EXISTS tile_sets_fk CASCADE;
ALTER TABLE public.many_tiles_has_many_tile_sets ADD CONSTRAINT tile_sets_fk FOREIGN KEY (id_tile_sets)
REFERENCES public.tile_sets (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: sessions_fk | type: CONSTRAINT --
-- ALTER TABLE public.invite_links DROP CONSTRAINT IF EXISTS sessions_fk CASCADE;
ALTER TABLE public.invite_links ADD CONSTRAINT sessions_fk FOREIGN KEY (id_sessions)
REFERENCES public.sessions (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: connections_fk | type: CONSTRAINT --
-- ALTER TABLE public.tiles DROP CONSTRAINT IF EXISTS connections_fk CASCADE;
ALTER TABLE public.tiles ADD CONSTRAINT connections_fk FOREIGN KEY (id_connections)
REFERENCES public.connections (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: connections_fk | type: CONSTRAINT --
-- ALTER TABLE public.tile_sets DROP CONSTRAINT IF EXISTS connections_fk CASCADE;
ALTER TABLE public.tile_sets ADD CONSTRAINT connections_fk FOREIGN KEY (id_connections)
REFERENCES public.connections (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: tile_sets_uq | type: CONSTRAINT --
-- ALTER TABLE public.tile_sets DROP CONSTRAINT IF EXISTS tile_sets_uq CASCADE;
ALTER TABLE public.tile_sets ADD CONSTRAINT tile_sets_uq UNIQUE (id_connections);
-- ddl-end --

-- object: users_fk | type: CONSTRAINT --
-- ALTER TABLE public.invite_links DROP CONSTRAINT IF EXISTS users_fk CASCADE;
ALTER TABLE public.invite_links ADD CONSTRAINT users_fk FOREIGN KEY (id_users)
REFERENCES public.users (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: users_fk | type: CONSTRAINT --
-- ALTER TABLE public.projects DROP CONSTRAINT IF EXISTS users_fk CASCADE;
ALTER TABLE public.projects ADD CONSTRAINT users_fk FOREIGN KEY (id_users)
REFERENCES public.users (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: users_fk | type: CONSTRAINT --
-- ALTER TABLE public.connections DROP CONSTRAINT IF EXISTS users_fk CASCADE;
ALTER TABLE public.connections ADD CONSTRAINT users_fk FOREIGN KEY (id_users)
REFERENCES public.users (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: public.many_sessions_has_many_tile_sets | type: TABLE --
-- DROP TABLE IF EXISTS public.many_sessions_has_many_tile_sets CASCADE;
CREATE TABLE public.many_sessions_has_many_tile_sets(

);
-- ddl-end --

-- object: id_sessions | type: COLUMN --
-- ALTER TABLE public.many_sessions_has_many_tile_sets DROP COLUMN IF EXISTS id_sessions CASCADE;
ALTER TABLE public.many_sessions_has_many_tile_sets ADD COLUMN id_sessions integer NOT NULL;
-- ddl-end --


-- object: id_tile_sets | type: COLUMN --
-- ALTER TABLE public.many_sessions_has_many_tile_sets DROP COLUMN IF EXISTS id_tile_sets CASCADE;
ALTER TABLE public.many_sessions_has_many_tile_sets ADD COLUMN id_tile_sets integer NOT NULL;
-- ddl-end --

-- object: many_sessions_has_many_tile_sets_pk | type: CONSTRAINT --
-- ALTER TABLE public.many_sessions_has_many_tile_sets DROP CONSTRAINT IF EXISTS many_sessions_has_many_tile_sets_pk CASCADE;
ALTER TABLE public.many_sessions_has_many_tile_sets ADD CONSTRAINT many_sessions_has_many_tile_sets_pk PRIMARY KEY (id_sessions,id_tile_sets);
-- ddl-end --


-- object: sessions_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_sessions_has_many_tile_sets DROP CONSTRAINT IF EXISTS sessions_fk CASCADE;
ALTER TABLE public.many_sessions_has_many_tile_sets ADD CONSTRAINT sessions_fk FOREIGN KEY (id_sessions)
REFERENCES public.sessions (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: tile_sets_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_sessions_has_many_tile_sets DROP CONSTRAINT IF EXISTS tile_sets_fk CASCADE;
ALTER TABLE public.many_sessions_has_many_tile_sets ADD CONSTRAINT tile_sets_fk FOREIGN KEY (id_tile_sets)
REFERENCES public.tile_sets (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --


