-- Fonction and trigger for synchronize id_project with project_id and id_user with user_id in project_members table
CREATE OR REPLACE FUNCTION public.project_members_sync ()
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
  IF NEW.id_users IS NULL THEN
     NEW.id_users := NEW.user_id;
  END IF;	    
  IF NEW.id_projects IS NULL THEN
     NEW.id_projects := NEW.project_id;
  END IF;	    
  RETURN NEW;
END;
$function$;
-- ddl-end --
ALTER FUNCTION public.project_members_sync() OWNER TO tiledviz;

-- object: trg_project_members_sync | type: TRIGGER --
-- DROP TRIGGER IF EXISTS trg_project_members_sync ON public.project_members CASCADE;
CREATE OR REPLACE TRIGGER trg_project_members_sync
	BEFORE INSERT OR UPDATE
	ON public.project_members
	FOR EACH ROW
	EXECUTE PROCEDURE public.project_members_sync();
-- ddl-end --
