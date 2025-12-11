-- Fonction et trigger pour ajouter automatiquement le créateur comme owner dans project_members

CREATE OR REPLACE FUNCTION add_owner_to_project_members()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO project_members (project_id, user_id, role_type, id_users, id_projects)
  VALUES (NEW.id, NEW.id_users, 'owner', NEW.id_users, NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_add_owner_to_project_members ON projects;
CREATE TRIGGER trg_add_owner_to_project_members
AFTER INSERT ON projects
FOR EACH ROW
EXECUTE FUNCTION add_owner_to_project_members();