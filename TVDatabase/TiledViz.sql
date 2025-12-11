-- ** Database generated with pgModeler (PostgreSQL Database Modeler).
-- ** pgModeler version: 1.2.0
-- ** PostgreSQL version: 17.0
-- ** Project Site: pgmodeler.io
-- ** Model Author: ---

-- ** Database creation must be performed outside a multi lined SQL file. 
-- ** These commands were put in this file only as a convenience.

-- object: "TiledViz" | type: DATABASE --
-- DROP DATABASE IF EXISTS "TiledViz";
CREATE DATABASE "TiledViz"
	ENCODING = 'UTF8'
	LC_COLLATE = 'en_US.utf8'
	LC_CTYPE = 'en_US.utf8'
	TABLESPACE = pg_default
	OWNER = tiledviz;
-- ddl-end --


SET check_function_bodies = false;
-- ddl-end --

SET search_path TO pg_catalog,public;
-- ddl-end --

-- object: public.add_owner_to_project_members | type: FUNCTION --
-- DROP FUNCTION IF EXISTS public.add_owner_to_project_members() CASCADE;
CREATE OR REPLACE FUNCTION public.add_owner_to_project_members ()
	RETURNS trigger
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS 
$function$
BEGIN
  INSERT INTO project_members (project_id, user_id, role_type)
  VALUES (NEW.id, NEW.id_users, 'owner');
  RETURN NEW;
END;
$function$;
-- ddl-end --
ALTER FUNCTION public.add_owner_to_project_members() OWNER TO tiledviz;
-- ddl-end --

-- object: public.delm2mfreetilesets | type: FUNCTION --
-- DROP FUNCTION IF EXISTS public.delm2mfreetilesets() CASCADE;
CREATE OR REPLACE FUNCTION public.delm2mfreetilesets ()
	RETURNS integer
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS 
$function$
DECLARE nb integer;
BEGIN
	nb := (SELECT COUNT(*) FROM freetilesets);
	DELETE FROM many_tiles_has_many_tile_sets
	WHERE id_tile_sets IN (SELECT id FROM freetilesets);
	RETURN  nb;
END;
$function$;
-- ddl-end --
ALTER FUNCTION public.delm2mfreetilesets() OWNER TO tiledviz;
-- ddl-end --

-- object: public.deltileset | type: FUNCTION --
-- DROP FUNCTION IF EXISTS public.deltileset(integer) CASCADE;
CREATE OR REPLACE FUNCTION public.deltileset (idts integer)
	RETURNS void
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS 
$function$
BEGIN
	DELETE FROM many_tiles_has_many_tile_sets WHERE id_tile_sets = $1;
	DELETE FROM many_sessions_has_many_tile_sets WHERE id_tile_sets = $1;
	DELETE FROM connections WHERE id = ( SELECT id_connections FROM tile_sets WHERE id = $1);
	DELETE FROM tile_sets WHERE id = $1;
END;
$function$;
-- ddl-end --
ALTER FUNCTION public.deltileset(integer) OWNER TO tiledviz;
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
CREATE TABLE public.tiles (
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
COMMENT ON COLUMN public.tiles.source IS E'source of the tile : may be an url or a path in a directory of initial conditions or a list of paths.';
-- ddl-end --
ALTER TABLE public.tiles OWNER TO tiledviz;
-- ddl-end --

-- object: public.listtileset | type: FUNCTION --
-- DROP FUNCTION IF EXISTS public.listtileset(integer) CASCADE;
CREATE OR REPLACE FUNCTION public.listtileset (idts integer)
	RETURNS SETOF public.tiles
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	ROWS 1000
	AS 
$function$
BEGIN
	RETURN QUERY ( SELECT *  FROM tiles t
  	WHERE (t.id IN ( SELECT tmt.id_tiles FROM many_tiles_has_many_tile_sets tmt WHERE id_tile_sets = $1)));
END;
$function$;
-- ddl-end --
ALTER FUNCTION public.listtileset(integer) OWNER TO tiledviz;
-- ddl-end --

-- object: public.viewtileset | type: FUNCTION --
-- DROP FUNCTION IF EXISTS public.viewtileset(integer) CASCADE;
CREATE OR REPLACE FUNCTION public.viewtileset (idts integer)
	RETURNS void
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS 
$function$
BEGIN
	DROP VIEW IF EXISTS thistileset;
	CREATE VIEW thistileset AS ( SELECT listtileset($1) );
END;
$function$;
-- ddl-end --
ALTER FUNCTION public.viewtileset(integer) OWNER TO tiledviz;
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
CREATE TABLE public.connections (
	id integer NOT NULL DEFAULT nextval('public.connections_id_seq'::regclass),
	creation_date timestamp,
	host_address character varying(60),
	auth_type character varying(10),
	container character varying(100),
	id_users integer NOT NULL,
	scheduler character varying(15),
	scheduler_file character varying(30),
	config_files json,
	connection_vnc smallint DEFAULT 0,
	CONSTRAINT connections_pkey PRIMARY KEY (id)
);
-- ddl-end --
ALTER TABLE public.connections OWNER TO tiledviz;
-- ddl-end --

-- object: public.many_tiles_has_many_tile_sets | type: TABLE --
-- DROP TABLE IF EXISTS public.many_tiles_has_many_tile_sets CASCADE;
CREATE TABLE public.many_tiles_has_many_tile_sets (
	id_tiles integer NOT NULL,
	id_tile_sets integer NOT NULL,
	CONSTRAINT many_tiles_has_many_tile_sets_pk PRIMARY KEY (id_tiles,id_tile_sets)
);
-- ddl-end --
ALTER TABLE public.many_tiles_has_many_tile_sets OWNER TO tiledviz;
-- ddl-end --

-- object: public.freetiles | type: VIEW --
-- DROP VIEW IF EXISTS public.freetiles CASCADE;
CREATE OR REPLACE VIEW public.freetiles
AS 
SELECT t.id,
    t.title
   FROM tiles t
  WHERE (NOT (t.id IN ( SELECT tmt.id_tiles
           FROM many_tiles_has_many_tile_sets tmt)));
-- ddl-end --
ALTER VIEW public.freetiles OWNER TO tiledviz;
-- ddl-end --

-- object: public.many_sessions_has_many_tile_sets | type: TABLE --
-- DROP TABLE IF EXISTS public.many_sessions_has_many_tile_sets CASCADE;
CREATE TABLE public.many_sessions_has_many_tile_sets (
	id_sessions integer NOT NULL,
	id_tile_sets integer NOT NULL,
	CONSTRAINT many_sessions_has_many_tile_sets_pk PRIMARY KEY (id_sessions,id_tile_sets)
);
-- ddl-end --
ALTER TABLE public.many_sessions_has_many_tile_sets OWNER TO tiledviz;
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
CREATE TABLE public.tile_sets (
	id integer NOT NULL DEFAULT nextval('public.tile_sets_id_seq'::regclass),
	name character varying(80) NOT NULL,
	type_of_tiles character varying(15) NOT NULL,
	"Dataset_path" character varying(100),
	id_connections integer,
	creation_date timestamp,
	source json,
	config_files json,
	launch_file character varying(30),
	CONSTRAINT tile_sets_pkey PRIMARY KEY (id),
	CONSTRAINT tile_sets_uq UNIQUE (id_connections)
);
-- ddl-end --
COMMENT ON COLUMN public.tile_sets.type_of_tiles IS E'must discribe the nature sources of the tiles connected for this tile_set. In this list : web png, local image, remote database file, set of database remote files';
-- ddl-end --
COMMENT ON COLUMN public.tile_sets."Dataset_path" IS E'Path of  the database for this tile_set.';
-- ddl-end --
ALTER TABLE public.tile_sets OWNER TO tiledviz;
-- ddl-end --

-- object: public.freetilesets | type: VIEW --
-- DROP VIEW IF EXISTS public.freetilesets CASCADE;
CREATE OR REPLACE VIEW public.freetilesets
AS 
SELECT ts.id,
    ts.name
   FROM tile_sets ts
  WHERE (NOT (ts.id IN ( SELECT smt.id_tile_sets
           FROM many_sessions_has_many_tile_sets smt)));
-- ddl-end --
ALTER VIEW public.freetilesets OWNER TO tiledviz;
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
CREATE TABLE public.invite_links (
	id integer NOT NULL DEFAULT nextval('public.invite_links_id_seq'::regclass),
	link character varying(200) NOT NULL,
	host_user character varying(80) NOT NULL,
	host_project character varying(80) NOT NULL,
	type boolean,
	creation_date timestamp,
	expiration_date timestamp,
	is_revoked boolean DEFAULT false,
	message character varying(500),
	target_email character varying(80),
	group_name character varying(80),
	id_sessions integer,
	id_users integer,
	max_uses integer DEFAULT 1,
	use_count integer DEFAULT 0,
	CONSTRAINT invite_links_link_key UNIQUE (link),
	CONSTRAINT invite_links_pkey PRIMARY KEY (id)
);
-- ddl-end --
COMMENT ON COLUMN public.invite_links.expiration_date IS E'Date after which the invite link expires';
-- ddl-end --
COMMENT ON COLUMN public.invite_links.is_revoked IS E'Whether the invite link has been revoked';
-- ddl-end --
COMMENT ON COLUMN public.invite_links.message IS E'Custom message to be sent with the invitation';
-- ddl-end --
COMMENT ON COLUMN public.invite_links.target_email IS E'Email address of the invited user';
-- ddl-end --
COMMENT ON COLUMN public.invite_links.group_name IS E'Name of the group if this is a group invitation';
-- ddl-end --
COMMENT ON COLUMN public.invite_links.max_uses IS E'Maximum number of times this invite link can be used';
-- ddl-end --
COMMENT ON COLUMN public.invite_links.use_count IS E'Number of times this invite link has been used';
-- ddl-end --
ALTER TABLE public.invite_links OWNER TO tiledviz;
-- ddl-end --

-- object: public.many_users_has_many_sessions | type: TABLE --
-- DROP TABLE IF EXISTS public.many_users_has_many_sessions CASCADE;
CREATE TABLE public.many_users_has_many_sessions (
	id_users integer NOT NULL,
	id_sessions integer NOT NULL,
	CONSTRAINT many_users_has_many_sessions_pk PRIMARY KEY (id_users,id_sessions)
);
-- ddl-end --
ALTER TABLE public.many_users_has_many_sessions OWNER TO tiledviz;
-- ddl-end --

-- object: public.project_members | type: TABLE --
-- DROP TABLE IF EXISTS public.project_members CASCADE;
CREATE TABLE public.project_members (
	project_id integer NOT NULL,
	user_id integer NOT NULL,
	role_type character varying(20) NOT NULL DEFAULT 'viewer',
	joined_at timestamp DEFAULT CURRENT_TIMESTAMP,
	id_users integer,
	id_projects integer,
	CONSTRAINT valid_member_role CHECK (((role_type)::text = ANY (ARRAY[('owner'::character varying)::text, ('admin'::character varying)::text, ('editor'::character varying)::text, ('viewer'::character varying)::text, ('guest'::character varying)::text]))),
	CONSTRAINT project_members_pkey PRIMARY KEY (project_id,user_id)
);
-- ddl-end --
COMMENT ON COLUMN public.project_members.project_id IS E'Reference to projects table';
-- ddl-end --
COMMENT ON COLUMN public.project_members.user_id IS E'Reference to users table';
-- ddl-end --
COMMENT ON COLUMN public.project_members.role_type IS E'Role of the user in this project';
-- ddl-end --
COMMENT ON COLUMN public.project_members.joined_at IS E'When the user joined the project';
-- ddl-end --
ALTER TABLE public.project_members OWNER TO tiledviz;
-- ddl-end --

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

-- object: public.projects | type: TABLE --
-- DROP TABLE IF EXISTS public.projects CASCADE;
CREATE TABLE public.projects (
	id integer NOT NULL DEFAULT nextval('public.projects_id_seq'::regclass),
	id_users integer,
	name character varying(80) NOT NULL,
	creation_date timestamp,
	description character varying(120),
	role_type character varying(20) NOT NULL,
	CONSTRAINT valid_role_type CHECK (((role_type)::text = ANY (ARRAY[('owner'::character varying)::text, ('admin'::character varying)::text, ('editor'::character varying)::text, ('viewer'::character varying)::text, ('guest'::character varying)::text]))),
	CONSTRAINT projects_pkey PRIMARY KEY (id),
	CONSTRAINT uniq_project UNIQUE (name)
);
-- ddl-end --
COMMENT ON COLUMN public.projects.role_type IS E'Type de rôle dans le projet';
-- ddl-end --
ALTER TABLE public.projects OWNER TO tiledviz;
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
CREATE TABLE public.users (
	id integer NOT NULL DEFAULT nextval('public.users_id_seq'::regclass),
	name character varying(80) NOT NULL,
	creation_date timestamp,
	mail character varying(80),
	compagny character varying,
	manager character varying(80),
	salt character(20) NOT NULL,
	password character(128),
	dateverified timestamp,
	is_admin boolean DEFAULT false,
	is_verified boolean NOT NULL DEFAULT False,
	CONSTRAINT uniq_users UNIQUE (name),
	CONSTRAINT users_pkey PRIMARY KEY (id)
);
-- ddl-end --
COMMENT ON COLUMN public.users.manager IS E'Project manager';
-- ddl-end --
COMMENT ON COLUMN public.users.is_admin IS E'Whether the user is an administrator';
-- ddl-end --
ALTER TABLE public.users OWNER TO tiledviz;
-- ddl-end --

-- object: public.project_members_detailed | type: VIEW --
-- DROP VIEW IF EXISTS public.project_members_detailed CASCADE;
CREATE OR REPLACE VIEW public.project_members_detailed
AS 
SELECT pm.project_id,
    p.name AS project_name,
    pm.user_id,
    u.name AS user_name,
    u.mail AS user_email,
    pm.role_type,
    pm.joined_at,
        CASE
            WHEN ((pm.role_type)::text = 'owner'::text) THEN 1
            WHEN ((pm.role_type)::text = 'admin'::text) THEN 2
            WHEN ((pm.role_type)::text = 'editor'::text) THEN 3
            WHEN ((pm.role_type)::text = 'viewer'::text) THEN 4
            WHEN ((pm.role_type)::text = 'guest'::text) THEN 5
            ELSE 6
        END AS role_priority
   FROM ((project_members pm
     JOIN projects p ON ((pm.project_id = p.id)))
     JOIN users u ON ((pm.user_id = u.id)))
  ORDER BY pm.project_id,
        CASE
            WHEN ((pm.role_type)::text = 'owner'::text) THEN 1
            WHEN ((pm.role_type)::text = 'admin'::text) THEN 2
            WHEN ((pm.role_type)::text = 'editor'::text) THEN 3
            WHEN ((pm.role_type)::text = 'viewer'::text) THEN 4
            WHEN ((pm.role_type)::text = 'guest'::text) THEN 5
            ELSE 6
        END, u.name;
-- ddl-end --
ALTER VIEW public.project_members_detailed OWNER TO tiledviz;
-- ddl-end --

-- object: public.project_owners_detailed | type: VIEW --
-- DROP VIEW IF EXISTS public.project_owners_detailed CASCADE;
CREATE OR REPLACE VIEW public.project_owners_detailed
AS 
SELECT p.id AS project_id,
    p.name AS project_name,
    p.description,
    p.creation_date AS project_created,
    u.id AS owner_id,
    u.name AS owner_name,
    u.mail AS owner_email,
    u.compagny AS owner_company,
    pm.joined_at AS ownership_date,
        CASE
            WHEN (pm.user_id IS NULL) THEN 'NO OWNER'::text
            ELSE 'HAS OWNER'::text
        END AS ownership_status
   FROM ((projects p
     LEFT JOIN project_members pm ON (((p.id = pm.project_id) AND ((pm.role_type)::text = ('owner'::character varying)::text))))
     LEFT JOIN users u ON ((pm.user_id = u.id)))
  ORDER BY
        CASE
            WHEN (pm.user_id IS NULL) THEN 'NO OWNER'::text
            ELSE 'HAS OWNER'::text
        END DESC, p.name;
-- ddl-end --
ALTER VIEW public.project_owners_detailed OWNER TO tiledviz;
-- ddl-end --

-- object: public.project_owners_summary | type: VIEW --
-- DROP VIEW IF EXISTS public.project_owners_summary CASCADE;
CREATE OR REPLACE VIEW public.project_owners_summary
AS 
SELECT p.id AS project_id,
    p.name AS project_name,
    p.creation_date,
    u.id AS owner_id,
    u.name AS owner_name,
    u.mail AS owner_email,
    pm.joined_at AS ownership_date
   FROM ((projects p
     LEFT JOIN project_members pm ON (((p.id = pm.project_id) AND ((pm.role_type)::text = ('owner'::character varying)::text))))
     LEFT JOIN users u ON ((pm.user_id = u.id)))
  ORDER BY p.name;
-- ddl-end --
ALTER VIEW public.project_owners_summary OWNER TO tiledviz;
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
CREATE TABLE public.sessions (
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
COMMENT ON COLUMN public.sessions."Number_of_active_users" IS E'Number of users actively connected to this sessions';
-- ddl-end --
COMMENT ON COLUMN public.sessions.timeout IS E'Set the timeout (in seconds) after which a session is disactivated (Number_of_active_users is 0) while no socket is still connected.';
-- ddl-end --
COMMENT ON COLUMN public.sessions.config IS E'configuration of the grid for this session';
-- ddl-end --
ALTER TABLE public.sessions OWNER TO tiledviz;
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

-- object: idx_project_members_composite | type: INDEX --
-- DROP INDEX IF EXISTS public.idx_project_members_composite CASCADE;
CREATE INDEX idx_project_members_composite ON public.project_members
USING btree
(
	project_id,
	user_id,
	role_type
)
WITH (FILLFACTOR = 90);
-- ddl-end --

-- object: idx_project_members_project | type: INDEX --
-- DROP INDEX IF EXISTS public.idx_project_members_project CASCADE;
CREATE INDEX idx_project_members_project ON public.project_members
USING btree
(
	project_id
)
WITH (FILLFACTOR = 90);
-- ddl-end --

-- object: idx_project_members_project_role | type: INDEX --
-- DROP INDEX IF EXISTS public.idx_project_members_project_role CASCADE;
CREATE INDEX idx_project_members_project_role ON public.project_members
USING btree
(
	project_id,
	role_type
)
WITH (FILLFACTOR = 90);
-- ddl-end --

-- object: idx_project_members_role | type: INDEX --
-- DROP INDEX IF EXISTS public.idx_project_members_role CASCADE;
CREATE INDEX idx_project_members_role ON public.project_members
USING btree
(
	role_type
)
WITH (FILLFACTOR = 90)
WHERE (role_type::text = ANY (ARRAY['owner'::text, 'admin'::text]));
-- ddl-end --

-- object: idx_project_members_user | type: INDEX --
-- DROP INDEX IF EXISTS public.idx_project_members_user CASCADE;
CREATE INDEX idx_project_members_user ON public.project_members
USING btree
(
	user_id
)
WITH (FILLFACTOR = 90);
-- ddl-end --

-- object: uq_project_owner | type: INDEX --
-- DROP INDEX IF EXISTS public.uq_project_owner CASCADE;
CREATE UNIQUE INDEX uq_project_owner ON public.project_members
USING btree
(
	project_id
)
WITH (FILLFACTOR = 90)
WHERE (role_type::text = 'owner'::text);
-- ddl-end --

-- object: trg_add_owner_to_project_members | type: TRIGGER --
-- DROP TRIGGER IF EXISTS trg_add_owner_to_project_members ON public.projects CASCADE;
CREATE OR REPLACE TRIGGER trg_add_owner_to_project_members
	AFTER INSERT 
	ON public.projects
	FOR EACH ROW
	EXECUTE PROCEDURE public.add_owner_to_project_members();
-- ddl-end --

-- object: connections_fk | type: CONSTRAINT --
-- ALTER TABLE public.tiles DROP CONSTRAINT IF EXISTS connections_fk CASCADE;
ALTER TABLE public.tiles ADD CONSTRAINT connections_fk FOREIGN KEY (id_connections)
REFERENCES public.connections (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: users_fk | type: CONSTRAINT --
-- ALTER TABLE public.connections DROP CONSTRAINT IF EXISTS users_fk CASCADE;
ALTER TABLE public.connections ADD CONSTRAINT users_fk FOREIGN KEY (id_users)
REFERENCES public.users (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: tile_sets_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_tiles_has_many_tile_sets DROP CONSTRAINT IF EXISTS tile_sets_fk CASCADE;
ALTER TABLE public.many_tiles_has_many_tile_sets ADD CONSTRAINT tile_sets_fk FOREIGN KEY (id_tile_sets)
REFERENCES public.tile_sets (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: tiles_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_tiles_has_many_tile_sets DROP CONSTRAINT IF EXISTS tiles_fk CASCADE;
ALTER TABLE public.many_tiles_has_many_tile_sets ADD CONSTRAINT tiles_fk FOREIGN KEY (id_tiles)
REFERENCES public.tiles (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
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

-- object: connections_fk | type: CONSTRAINT --
-- ALTER TABLE public.tile_sets DROP CONSTRAINT IF EXISTS connections_fk CASCADE;
ALTER TABLE public.tile_sets ADD CONSTRAINT connections_fk FOREIGN KEY (id_connections)
REFERENCES public.connections (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: sessions_fk | type: CONSTRAINT --
-- ALTER TABLE public.invite_links DROP CONSTRAINT IF EXISTS sessions_fk CASCADE;
ALTER TABLE public.invite_links ADD CONSTRAINT sessions_fk FOREIGN KEY (id_sessions)
REFERENCES public.sessions (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: users_fk | type: CONSTRAINT --
-- ALTER TABLE public.invite_links DROP CONSTRAINT IF EXISTS users_fk CASCADE;
ALTER TABLE public.invite_links ADD CONSTRAINT users_fk FOREIGN KEY (id_users)
REFERENCES public.users (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: sessions_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_users_has_many_sessions DROP CONSTRAINT IF EXISTS sessions_fk CASCADE;
ALTER TABLE public.many_users_has_many_sessions ADD CONSTRAINT sessions_fk FOREIGN KEY (id_sessions)
REFERENCES public.sessions (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: users_fk | type: CONSTRAINT --
-- ALTER TABLE public.many_users_has_many_sessions DROP CONSTRAINT IF EXISTS users_fk CASCADE;
ALTER TABLE public.many_users_has_many_sessions ADD CONSTRAINT users_fk FOREIGN KEY (id_users)
REFERENCES public.users (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: project_members_project_fk | type: CONSTRAINT --
-- ALTER TABLE public.project_members DROP CONSTRAINT IF EXISTS project_members_project_fk CASCADE;
ALTER TABLE public.project_members ADD CONSTRAINT project_members_project_fk FOREIGN KEY (project_id)
REFERENCES public.projects (id) MATCH SIMPLE
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --

-- object: project_members_user_fk | type: CONSTRAINT --
-- ALTER TABLE public.project_members DROP CONSTRAINT IF EXISTS project_members_user_fk CASCADE;
ALTER TABLE public.project_members ADD CONSTRAINT project_members_user_fk FOREIGN KEY (user_id)
REFERENCES public.users (id) MATCH SIMPLE
ON DELETE NO ACTION ON UPDATE NO ACTION;
-- ddl-end --

-- object: projects_fk | type: CONSTRAINT --
-- ALTER TABLE public.project_members DROP CONSTRAINT IF EXISTS projects_fk CASCADE;
ALTER TABLE public.project_members ADD CONSTRAINT projects_fk FOREIGN KEY (id_projects)
REFERENCES public.projects (id) MATCH FULL
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --

-- object: users_fk | type: CONSTRAINT --
-- ALTER TABLE public.project_members DROP CONSTRAINT IF EXISTS users_fk CASCADE;
ALTER TABLE public.project_members ADD CONSTRAINT users_fk FOREIGN KEY (id_users)
REFERENCES public.users (id) MATCH FULL
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --

-- object: users_fk | type: CONSTRAINT --
-- ALTER TABLE public.projects DROP CONSTRAINT IF EXISTS users_fk CASCADE;
ALTER TABLE public.projects ADD CONSTRAINT users_fk FOREIGN KEY (id_users)
REFERENCES public.users (id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: projects_fk | type: CONSTRAINT --
-- ALTER TABLE public.sessions DROP CONSTRAINT IF EXISTS projects_fk CASCADE;
ALTER TABLE public.sessions ADD CONSTRAINT projects_fk FOREIGN KEY (id_projects)
REFERENCES public.projects (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --


