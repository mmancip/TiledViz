-- object: public.freetiles | type: VIEW --
-- DROP VIEW IF EXISTS public.freetiles CASCADE;
CREATE VIEW public.freetiles
AS
SELECT t.id,t.title
       FROM tiles t
      WHERE (NOT (t.id IN ( SELECT tmt.id_tiles
      	    FROM many_tiles_has_many_tile_sets tmt)));

-- ddl-end --
ALTER VIEW public.freetiles OWNER TO tiledviz;
-- ddl-end --
		    
-- object: public.freetilesets | type: VIEW --
-- DROP VIEW IF EXISTS public.freetilesets CASCADE;
CREATE VIEW public.freetilesets
AS
SELECT ts.id,ts.name
       FROM tile_sets ts
      WHERE (NOT (ts.id IN ( SELECT smt.id_tile_sets
      	    FROM many_sessions_has_many_tile_sets smt)));

-- ddl-end --
ALTER VIEW public.freetilesets OWNER TO tiledviz;
-- ddl-end --

CREATE FUNCTION public.delm2mfreetilesets ()
       RETURNS integer
       LANGUAGE plpgsql
       VOLATILE
       CALLED ON NULL INPUT
       SECURITY INVOKER
       COST 100
       AS $$
DECLARE nb integer;
BEGIN
	nb := (SELECT COUNT(*) FROM freetilesets);
	DELETE FROM many_tiles_has_many_tile_sets
	WHERE id_tile_sets IN (SELECT id FROM freetilesets);
	RETURN  nb;
END;
$$;

-- ddl-end --
ALTER FUNCTION public.delm2mfreetilesets() OWNER TO tiledviz;
-- ddl-end --

-- object: public.deltileset | type: FUNCTION --
-- DROP FUNCTION IF EXISTS public.deltileset(integer) CASCADE;
CREATE FUNCTION public.deltileset ( idts integer)
       RETURNS void
       LANGUAGE plpgsql
       VOLATILE
       CALLED ON NULL INPUT
       SECURITY INVOKER
       COST 100
       AS $$
BEGIN
	DELETE FROM many_tiles_has_many_tile_sets WHERE id_tile_sets = $1;
	DELETE FROM many_sessions_has_many_tile_sets WHERE id_tile_sets = $1;
	DELETE FROM connections WHERE id = ( SELECT id_connections FROM tile_sets WHERE id = $1);
	DELETE FROM tile_sets WHERE id = $1;
END;
$$;

-- ddl-end --
ALTER FUNCTION public.deltileset(integer) OWNER TO tiledviz;
-- ddl-end --


-- object: public.listtileset | type: FUNCTION --
-- DROP FUNCTION IF EXISTS public.listtileset(integer) CASCADE;
CREATE FUNCTION public.listtileset ( idts integer)
       RETURNS SETOF public.tiles
       LANGUAGE plpgsql
       VOLATILE
       CALLED ON NULL INPUT
       SECURITY INVOKER
       COST 100
       ROWS 1000
       AS $$
BEGIN
	RETURN QUERY ( SELECT *  FROM tiles t
  	WHERE (t.id IN ( SELECT tmt.id_tiles FROM many_tiles_has_many_tile_sets tmt WHERE id_tile_sets = $1)));
END;
$$;

-- ddl-end --
ALTER FUNCTION public.listtileset(integer) OWNER TO tiledviz;
-- ddl-end --

-- object: public.viewtileset | type: FUNCTION --
-- DROP FUNCTION IF EXISTS public.viewtileset(integer) CASCADE;
CREATE FUNCTION public.viewtileset ( idts integer)
       RETURNS void
       LANGUAGE plpgsql
       VOLATILE
       CALLED ON NULL INPUT
       SECURITY INVOKER
       COST 100
       AS $$
BEGIN
	DROP VIEW IF EXISTS thistileset;
	CREATE VIEW thistileset AS ( SELECT listtileset($1) );
END;
$$;

-- ddl-end --
ALTER FUNCTION public.viewtileset(integer) OWNER TO tiledviz;
-- ddl-end --

