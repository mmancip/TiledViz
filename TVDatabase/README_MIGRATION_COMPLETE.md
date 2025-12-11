# TiledViz Database Migration Guide
## Master → Member-Management1 System

### Overview

This document explains the complete migration process from the old TiledViz system (Master branch) to the new member-management system (Member-Management1 branch). The migration adds comprehensive project member management with role-based access control.

---

##  Migration Objectives

### What the Migration Does:
1. **Adds `role_type` column** to the `projects` table
2. **Creates `project_members` table** for detailed member management
3. **Assigns project owners** to all existing projects
4. **Handles orphaned projects** by assigning them to a system admin
5. **Creates management views** for easy project oversight
6. **Adds performance indexes** for optimal query performance
7. **Sets up automatic triggers** for new project creation

### Key Features Added:
- **Role-based access control**: `owner`, `admin`, `editor`, `viewer`, `guest`
- **Project ownership tracking**: Clear ownership history and status
- **Member management views**: Easy-to-use views for project administration
- **Automatic assignment**: Triggers ensure new projects get proper owners
- **Performance optimization**: Indexes for fast member lookups

---

##  Files Involved

### Source Files:
- `TiledViz_master.sql` - Old database schema (Master branch)
- `TiledViz.sql` - New database schema (Member-Management1 branch)
- `complete_migration_script.sql` - **Main migration script**

- `README_MIGRATION_COMPLETE.md` - This documentation

---

##  Migration Process

### Step 1: Schema Migration
```sql
-- Adds role_type column to projects table
ALTER TABLE projects ADD COLUMN role_type character varying(20) NOT NULL DEFAULT 'owner';
```

### Step 2: New Tables Creation
```sql
-- Creates project_members table with full structure
CREATE TABLE project_members (
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    role_type character varying(20) NOT NULL DEFAULT 'viewer',
    joined_at timestamp DEFAULT CURRENT_TIMESTAMP,
    id_users integer,
    id_projects integer,
    -- ... constraints and indexes
);
```

### Step 3: Views Creation
- `project_members_detailed` - Complete member information with role priorities
- `project_owners_detailed` - Project ownership details with status
- `project_owners_summary` - Simplified ownership overview

### Step 4: Data Migration
- **Existing owners**: Projects with `id_users` become `owner` in `project_members`
- **Orphaned projects**: Assigned to `system_admin` user
- **Session participants**: Added as `viewer` role
- **Connection owners**: Added as `editor` role

### Step 5: Performance Optimization
- **5 specialized indexes** for fast queries
- **Foreign key constraints** for data integrity
- **Unique constraints** ensuring one owner per project

---

##  Testing Process

### Prerequisites
```bash
# Ensure PostgreSQL is running
sudo systemctl status postgresql

# Ensure tiledviz user exists
sudo -u postgres psql -c "\du" | grep tiledviz
```

##  Testing Process

### 1. Prepare Test Environment
```bash
# Create test database
sudo -u postgres psql -c "CREATE DATABASE tiledviz_test;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tiledviz_test TO tiledviz;"

# Load old schema
sudo -u postgres psql -d tiledviz_test -f /tmp/TiledViz_master.sql
```

### 2. Insert Test Data
```sql
-- Connect to test database
sudo -u postgres psql -d tiledviz_test

-- Insert test users
INSERT INTO users (name, creation_date, mail, salt, password, is_admin) VALUES 
('admin_user', NOW(), 'admin@test.com', 'salt123', 'password123', true),
('user1', NOW(), 'user1@test.com', 'salt456', 'password456', false),
('user2', NOW(), 'user2@test.com', 'salt789', 'password789', false),
('user3', NOW(), 'user3@test.com', 'salt000', 'password000', false);

-- Insert test projects (mix of owned and orphaned)
INSERT INTO projects (name, creation_date, description, id_users) VALUES 
('Projet A', NOW(), 'Description du projet A', 1),
('Projet B', NOW(), 'Description du projet B', 2),
('Projet C', NOW(), 'Description du projet C', 3),
('Projet Orphelin 1', NOW(), 'Projet sans propriétaire 1', NULL),
('Projet Orphelin 2', NOW(), 'Projet sans propriétaire 2', NULL);

-- Insert test sessions
INSERT INTO sessions (name, id_projects, creation_date, description) VALUES 
('Session 1', 1, NOW(), 'Session du projet A'),
('Session 2', 2, NOW(), 'Session du projet B'),
('Session 3', 3, NOW(), 'Session du projet C'),
('Session 4', 4, NOW(), 'Session du projet orphelin 1'),
('Session 5', 5, NOW(), 'Session du projet orphelin 2');

-- Insert test connections
INSERT INTO connections (creation_date, host_address, auth_type, id_users) VALUES 
(NOW(), '192.168.1.1', 'ssh', 1),
(NOW(), '192.168.1.2', 'ssh', 2),
(NOW(), '192.168.1.3', 'ssh', 3);

-- Insert test tile_sets
INSERT INTO tile_sets (name, type_of_tiles, id_connections, creation_date) VALUES 
('TileSet 1', 'web_png', 1, NOW()),
('TileSet 2', 'local_image', 2, NOW()),
('TileSet 3', 'remote_db', 3, NOW());

-- Insert test tiles
INSERT INTO tiles (title, pos_px_x, pos_px_y, source, id_connections, creation_date) VALUES 
('Tile 1', 100, 200, '{"url": "http://example.com/tile1.png"}', 1, NOW()),
('Tile 2', 300, 400, '{"path": "/data/tile2.png"}', 2, NOW()),
('Tile 3', 500, 600, '{"db": "remote_db_1"}', 3, NOW());

-- Insert many-to-many relationships
INSERT INTO many_users_has_many_sessions (id_users, id_sessions) VALUES 
(1, 1), (2, 2), (3, 3), (1, 4), (2, 5);

INSERT INTO many_sessions_has_many_tile_sets (id_sessions, id_tile_sets) VALUES 
(1, 1), (2, 2), (3, 3);

INSERT INTO many_tiles_has_many_tile_sets (id_tiles, id_tile_sets) VALUES 
(1, 1), (2, 2), (3, 3);
```

### 3. Execute Migration
```bash
# Copy migration script to accessible location
sudo cp TVDatabase/complete_migration_script.sql /tmp/
sudo chmod 644 /tmp/complete_migration_script.sql

# Execute migration
sudo -u postgres psql -d tiledviz_test -f /tmp/complete_migration_script.sql
```


---

##  Migration Validation

### Essential Validation Queries

#### 1. Check Migration Success
```sql
-- Overall migration status
SELECT 
    'Migration completed successfully!' as status,
    COUNT(*) as total_projects,
    COUNT(CASE WHEN u.name = 'system_admin' THEN 1 END) as orphaned_projects,
    COUNT(CASE WHEN u.name != 'system_admin' THEN 1 END) as regular_projects
FROM projects p
JOIN users u ON p.id_users = u.id;
```

#### 2. Verify Project Members Table
```sql
-- Check project_members table structure
\d project_members

-- Check all project members
SELECT * FROM project_members ORDER BY project_id, role_type;
```

#### 3. Verify No Orphaned Projects
```sql
-- Should return 0 rows
SELECT * FROM projects WHERE id_users IS NULL;
```

#### 4. Check Project Ownership
```sql
-- Detailed ownership information
SELECT * FROM project_owners_detailed ORDER BY project_id;

-- Summary ownership information
SELECT * FROM project_owners_summary ORDER BY project_name;
```

#### 5. Verify Member Roles
```sql
-- Check role assignments
SELECT 
    p.name as project_name,
    u.name as user_name,
    pm.role_type,
    pm.joined_at
FROM project_members pm
JOIN projects p ON pm.project_id = p.id
JOIN users u ON pm.user_id = u.id
ORDER BY p.name, pm.role_type;
```

#### 6. Check Views Functionality
```sql
-- Test project_members_detailed view
SELECT * FROM project_members_detailed ORDER BY project_id, role_priority;

-- Test project_owners_detailed view
SELECT * FROM project_owners_detailed ORDER BY ownership_status DESC, project_name;

-- Test project_owners_summary view
SELECT * FROM project_owners_summary ORDER BY project_name;
```

#### 7. Verify Indexes
```sql
-- Check indexes were created
SELECT indexname, tablename, indexdef 
FROM pg_indexes 
WHERE tablename = 'project_members' 
ORDER BY indexname;
```

#### 8. Verify Constraints
```sql
-- Check foreign key constraints
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name = 'project_members';
```

#### 9. Verify Triggers
```sql
-- Check triggers are active
SELECT 
    trigger_name, 
    event_manipulation, 
    action_timing, 
    action_statement
FROM information_schema.triggers 
WHERE event_object_table = 'projects';
```

#### 10. Test New Project Creation
```sql
-- Test trigger functionality
INSERT INTO projects (name, creation_date, description, id_users) 
VALUES ('Test Project', NOW(), 'Testing trigger', 1);

-- Verify owner was automatically added
SELECT * FROM project_members WHERE project_id = (SELECT id FROM projects WHERE name = 'Test Project');
```

---

##  Expected Results

### Successful Migration Should Show:
-  **0 orphaned projects** (all projects have owners)
-  **All existing owners** in `project_members` with `owner` role
-  **Orphaned projects** assigned to `system_admin`
-  **Session participants** as `viewer` role
-  **Connection owners** as `editor` role
-  **All views** working correctly
-  **All indexes** created
-  **All constraints** active
-  **Triggers** functioning

### Sample Expected Output:
```
 status               | total_projects | orphaned_projects | regular_projects 
---------------------+----------------+-------------------+------------------
 Migration completed! |              5 |                 2 |                3
```

---

##  Troubleshooting

### Common Issues:

#### 1. Permission Errors
```bash
# Solution: Ensure proper permissions
sudo chmod 644 /tmp/complete_migration_script.sql
sudo -u postgres psql -d tiledviz_test -f /tmp/complete_migration_script.sql
```

#### 2. Constraint Errors
```sql
-- Check for existing constraints
SELECT constraint_name FROM information_schema.table_constraints 
WHERE table_name = 'project_members';
```

#### 3. View Errors
```sql
-- Recreate views if needed
\i /tmp/complete_migration_script.sql
```

#### 4. Data Integrity Issues
```sql
-- Check for orphaned references
SELECT * FROM project_members pm 
LEFT JOIN projects p ON pm.project_id = p.id 
WHERE p.id IS NULL;
```

---

##  Rollback Procedure

If migration needs to be rolled back:

```sql
-- Remove new elements
DROP VIEW IF EXISTS project_owners_summary CASCADE;
DROP VIEW IF EXISTS project_owners_detailed CASCADE;
DROP VIEW IF EXISTS project_members_detailed CASCADE;

DROP TRIGGER IF EXISTS trg_add_owner_to_project_members ON projects;
DROP FUNCTION IF EXISTS add_owner_to_project_members();

DROP TABLE IF EXISTS project_members CASCADE;

-- Remove role_type column
ALTER TABLE projects DROP COLUMN IF EXISTS role_type;

-- Remove system_admin user
DELETE FROM users WHERE name = 'system_admin';
```

---


