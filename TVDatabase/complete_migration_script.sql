-- =====================================================
-- TiledViz Complete Migration Script
-- Master → Member-Management1 System
-- =====================================================
-- This script performs a complete migration from the old system
-- to the new member-management system with proper owner assignment
-- =====================================================

-- Start transaction for rollback capability
BEGIN;

-- =====================================================
-- STEP 1: Migrate Existing Table Structure
-- =====================================================

-- Add role_type column to projects table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'projects' AND column_name = 'role_type'
    ) THEN
        ALTER TABLE projects ADD COLUMN role_type character varying(20) NOT NULL DEFAULT 'owner';
        
        -- Add constraint for valid role types
        ALTER TABLE projects ADD CONSTRAINT valid_role_type CHECK (
            (role_type)::text = ANY (ARRAY[
                ('owner'::character varying)::text, 
                ('admin'::character varying)::text, 
                ('editor'::character varying)::text, 
                ('viewer'::character varying)::text, 
                ('guest'::character varying)::text
            ])
        );
        
        -- Set role_type to 'owner' for all existing projects with owners
        UPDATE projects SET role_type = 'owner' WHERE id_users IS NOT NULL;
        
        RAISE NOTICE 'Added role_type column to projects table';
    ELSE
        RAISE NOTICE 'role_type column already exists in projects table';
    END IF;
END $$;

-- =====================================================
-- STEP 2: Create New Tables and Functions
-- =====================================================

-- Create project_members table if it doesn't exist
CREATE TABLE IF NOT EXISTS project_members (
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    role_type character varying(20) NOT NULL DEFAULT 'viewer',
    joined_at timestamp DEFAULT CURRENT_TIMESTAMP,
    id_users integer,
    id_projects integer,
    CONSTRAINT valid_member_role CHECK (((role_type)::text = ANY (ARRAY[('owner'::character varying)::text, ('admin'::character varying)::text, ('editor'::character varying)::text, ('viewer'::character varying)::text, ('guest'::character varying)::text]))),
    CONSTRAINT project_members_pkey PRIMARY KEY (project_id,user_id)
);

-- Add comments to project_members columns
COMMENT ON COLUMN project_members.project_id IS 'Reference to projects table';
COMMENT ON COLUMN project_members.user_id IS 'Reference to users table';
COMMENT ON COLUMN project_members.role_type IS 'Role of the user in this project';
COMMENT ON COLUMN project_members.joined_at IS 'When the user joined the project';

-- Create the trigger function for automatic owner assignment
CREATE OR REPLACE FUNCTION add_owner_to_project_members()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- Automatically add the project owner to project_members table
    INSERT INTO project_members (project_id, user_id, role_type)
    VALUES (NEW.id, NEW.id_users, 'owner')
    ON CONFLICT (project_id, user_id) DO UPDATE SET
        role_type = 'owner',
        joined_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

-- Create the trigger
DROP TRIGGER IF EXISTS trg_add_owner_to_project_members ON projects;
CREATE TRIGGER trg_add_owner_to_project_members
    AFTER INSERT OR UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION add_owner_to_project_members();

-- =====================================================
-- STEP 2.1: Create Views
-- =====================================================

-- Create project_members_detailed view
CREATE OR REPLACE VIEW project_members_detailed AS
SELECT 
    pm.project_id,
    p.name AS project_name,
    pm.user_id,
    u.name AS user_name,
    u.mail AS user_email,
    pm.role_type,
    pm.joined_at,
    CASE
        WHEN pm.role_type = 'owner' THEN 1
        WHEN pm.role_type = 'admin' THEN 2
        WHEN pm.role_type = 'editor' THEN 3
        WHEN pm.role_type = 'viewer' THEN 4
        WHEN pm.role_type = 'guest' THEN 5
        ELSE 6
    END AS role_priority
FROM project_members pm
JOIN projects p ON pm.project_id = p.id
JOIN users u ON pm.user_id = u.id
ORDER BY pm.project_id, role_priority, u.name;

-- Create project_owners_detailed view
CREATE OR REPLACE VIEW project_owners_detailed AS
SELECT 
    p.id AS project_id,
    p.name AS project_name,
    p.description,
    p.creation_date AS project_created,
    u.id AS owner_id,
    u.name AS owner_name,
    u.mail AS owner_email,
    u.compagny AS owner_company,
    pm.joined_at AS ownership_date,
    CASE
        WHEN pm.user_id IS NULL THEN 'NO OWNER'
        ELSE 'HAS OWNER'
    END AS ownership_status
FROM projects p
LEFT JOIN project_members pm ON (p.id = pm.project_id AND pm.role_type = 'owner')
LEFT JOIN users u ON pm.user_id = u.id
ORDER BY ownership_status DESC, p.name;

-- Create project_owners_summary view
CREATE OR REPLACE VIEW project_owners_summary AS
SELECT 
    p.id AS project_id,
    p.name AS project_name,
    p.creation_date,
    u.id AS owner_id,
    u.name AS owner_name,
    u.mail AS owner_email,
    pm.joined_at AS ownership_date
FROM projects p
LEFT JOIN project_members pm ON (p.id = pm.project_id AND pm.role_type = 'owner')
LEFT JOIN users u ON pm.user_id = u.id
ORDER BY p.name;

-- =====================================================
-- STEP 3: Create Default System Admin User
-- =====================================================

-- Create a system admin user for orphaned projects
INSERT INTO users (name, creation_date, mail, salt, password, is_admin)
VALUES (
    'system_admin', 
    CURRENT_TIMESTAMP, 
    'admin@tiledviz.local', 
    'default_salt_12345', 
    'default_password_hash', 
    true
)
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- STEP 4: Migrate Project Ownership
-- =====================================================

-- Strategy: Only assign system_admin to truly orphaned projects (id_users IS NULL)
-- Projects with existing id_users keep their current owner
UPDATE projects 
SET id_users = (
    SELECT id FROM users WHERE name = 'system_admin' LIMIT 1
)
WHERE id_users IS NULL;

-- =====================================================
-- STEP 5: Populate Project Members for All Projects
-- =====================================================

-- IMPORTANT: The trigger only works for NEW projects, not existing ones
-- We need to manually populate project_members for all existing projects

-- 5.1: Add project owners (both existing and newly assigned)
INSERT INTO project_members (project_id, user_id, role_type)
SELECT id, id_users, 'owner'
FROM projects
WHERE id_users IS NOT NULL
ON CONFLICT (project_id, user_id) DO UPDATE SET
    role_type = 'owner',
    joined_at = CURRENT_TIMESTAMP;

-- 5.2: Add session participants as viewers (based on many_users_has_many_sessions)
-- This handles users who were participating in sessions but weren't project owners
INSERT INTO project_members (project_id, user_id, role_type)
SELECT DISTINCT s.id_projects, mus.id_users, 'viewer'
FROM many_users_has_many_sessions mus
JOIN sessions s ON mus.id_sessions = s.id
WHERE NOT EXISTS (
    SELECT 1 FROM project_members pm 
    WHERE pm.project_id = s.id_projects AND pm.user_id = mus.id_users
)
ON CONFLICT (project_id, user_id) DO UPDATE SET
    role_type = 'viewer',
    joined_at = CURRENT_TIMESTAMP;

-- 5.3: Add connection owners as editors (if they're not already project owners)
-- This handles users who created connections for the project
INSERT INTO project_members (project_id, user_id, role_type)
SELECT DISTINCT s.id_projects, c.id_users, 'editor'
FROM connections c
JOIN tile_sets ts ON c.id = ts.id_connections
JOIN many_sessions_has_many_tile_sets mst ON ts.id = mst.id_tile_sets
JOIN sessions s ON mst.id_sessions = s.id
WHERE NOT EXISTS (
    SELECT 1 FROM project_members pm 
    WHERE pm.project_id = s.id_projects AND pm.user_id = c.id_users
)
ON CONFLICT (project_id, user_id) DO UPDATE SET
    role_type = 'editor',
    joined_at = CURRENT_TIMESTAMP;

-- =====================================================
-- STEP 6: Create Indexes and Constraints
-- =====================================================

-- Create indexes for project_members table
CREATE INDEX IF NOT EXISTS idx_project_members_composite ON project_members (project_id, user_id, role_type) WITH (FILLFACTOR = 90);
CREATE INDEX IF NOT EXISTS idx_project_members_project ON project_members (project_id) WITH (FILLFACTOR = 90);
CREATE INDEX IF NOT EXISTS idx_project_members_project_role ON project_members (project_id, role_type) WITH (FILLFACTOR = 90);
CREATE INDEX IF NOT EXISTS idx_project_members_role ON project_members (role_type) WITH (FILLFACTOR = 90) WHERE role_type IN ('owner', 'admin');
CREATE INDEX IF NOT EXISTS idx_project_members_user ON project_members (user_id) WITH (FILLFACTOR = 90);

-- Create unique index for project owners (one owner per project)
CREATE UNIQUE INDEX IF NOT EXISTS uq_project_owner ON project_members (project_id) WITH (FILLFACTOR = 90) WHERE role_type = 'owner';

-- Add foreign key constraints for project_members
DO $$
BEGIN
    -- Add project_members_project_fk constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'project_members_project_fk' AND table_name = 'project_members'
    ) THEN
        ALTER TABLE project_members ADD CONSTRAINT project_members_project_fk 
            FOREIGN KEY (project_id) REFERENCES projects (id) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
    END IF;

    -- Add project_members_user_fk constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'project_members_user_fk' AND table_name = 'project_members'
    ) THEN
        ALTER TABLE project_members ADD CONSTRAINT project_members_user_fk 
            FOREIGN KEY (user_id) REFERENCES users (id) MATCH SIMPLE ON DELETE NO ACTION ON UPDATE NO ACTION;
    END IF;

    -- Add projects_fk constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'projects_fk' AND table_name = 'project_members'
    ) THEN
        ALTER TABLE project_members ADD CONSTRAINT projects_fk 
            FOREIGN KEY (id_projects) REFERENCES projects (id) MATCH FULL ON DELETE CASCADE ON UPDATE CASCADE;
    END IF;

    -- Add users_fk constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'users_fk' AND table_name = 'project_members'
    ) THEN
        ALTER TABLE project_members ADD CONSTRAINT users_fk 
            FOREIGN KEY (id_users) REFERENCES users (id) MATCH FULL ON DELETE CASCADE ON UPDATE CASCADE;
    END IF;
END $$;

-- =====================================================
-- STEP 7: Create Migration Log Table
-- =====================================================

-- Create a table to track migration progress
CREATE TABLE IF NOT EXISTS migration_log (
    id SERIAL PRIMARY KEY,
    migration_step VARCHAR(100) NOT NULL,
    description TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'SUCCESS'
);

-- Log the migration steps
INSERT INTO migration_log (migration_step, description) VALUES
('owner_assignment', 'Project owners assigned and project_members populated'),
('system_admin_created', 'Default system admin user created for orphaned projects'),
('triggers_created', 'Automatic owner assignment triggers created'),
('views_created', 'All project management views created'),
('indexes_created', 'Performance indexes created for project_members');

-- =====================================================
-- STEP 8: Validation Queries
-- =====================================================

-- Create a view to validate the migration
CREATE OR REPLACE VIEW migration_validation AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    u.name as owner_name,
    u.mail as owner_email,
    pm.role_type,
    pm.joined_at,
    CASE 
        WHEN u.name = 'system_admin' THEN 'ORPHANED_PROJECT'
        ELSE 'REGULAR_PROJECT'
    END as project_type
FROM projects p
LEFT JOIN users u ON p.id_users = u.id
LEFT JOIN project_members pm ON (p.id = pm.project_id AND pm.role_type = 'owner')
ORDER BY p.id;

-- =====================================================
-- STEP 9: Generate Migration Report
-- =====================================================

-- Create a comprehensive migration report
DO $$
DECLARE
    total_projects INTEGER;
    orphaned_projects INTEGER;
    regular_projects INTEGER;
    system_admin_id INTEGER;
BEGIN
    -- Get counts
    SELECT COUNT(*) INTO total_projects FROM projects;
    SELECT COUNT(*) INTO orphaned_projects FROM projects p JOIN users u ON p.id_users = u.id WHERE u.name = 'system_admin';
    SELECT COUNT(*) INTO regular_projects FROM projects p JOIN users u ON p.id_users = u.id WHERE u.name != 'system_admin';
    SELECT id INTO system_admin_id FROM users WHERE name = 'system_admin';
    
    -- Log the report
    INSERT INTO migration_log (migration_step, description) VALUES
    ('migration_report', 
     'Total projects: ' || total_projects || 
     ', Regular projects: ' || regular_projects || 
     ', Orphaned projects: ' || orphaned_projects ||
     ', System admin ID: ' || system_admin_id);
    
    -- Output the report
    RAISE NOTICE '=== MIGRATION REPORT ===';
    RAISE NOTICE 'Total projects migrated: %', total_projects;
    RAISE NOTICE 'Regular projects (with owners): %', regular_projects;
    RAISE NOTICE 'Orphaned projects (assigned to system admin): %', orphaned_projects;
    RAISE NOTICE 'System admin user ID: %', system_admin_id;
    RAISE NOTICE '=== MIGRATION COMPLETE ===';
END $$;

-- =====================================================
-- STEP 10: Create Helper Functions
-- =====================================================

-- Function to get project owner information
CREATE OR REPLACE FUNCTION get_project_owner(project_id INTEGER)
RETURNS TABLE (
    project_name VARCHAR(80),
    owner_name VARCHAR(80),
    owner_email VARCHAR(80),
    role_type VARCHAR(20),
    joined_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.name,
        u.name,
        u.mail,
        pm.role_type,
        pm.joined_at
    FROM projects p
    JOIN users u ON p.id_users = u.id
    JOIN project_members pm ON (p.id = pm.project_id AND pm.role_type = 'owner')
    WHERE p.id = project_id;
END;
$$ LANGUAGE plpgsql;

-- Function to check if a user is project owner
CREATE OR REPLACE FUNCTION is_project_owner(project_id INTEGER, user_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM project_members 
        WHERE project_id = $1 AND user_id = $2 AND role_type = 'owner'
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMMIT TRANSACTION
-- =====================================================

-- If we reach here, the migration was successful
COMMIT;

-- =====================================================
-- POST-MIGRATION VALIDATION
-- =====================================================

-- Display the migration results
SELECT 
    'Migration completed successfully!' as status,
    COUNT(*) as total_projects,
    COUNT(CASE WHEN u.name = 'system_admin' THEN 1 END) as orphaned_projects,
    COUNT(CASE WHEN u.name != 'system_admin' THEN 1 END) as regular_projects
FROM projects p
JOIN users u ON p.id_users = u.id;

-- Show all project owners using the new views
SELECT * FROM project_owners_detailed ORDER BY project_id;

-- =====================================================
-- END OF MIGRATION SCRIPT
-- =====================================================
