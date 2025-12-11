"""
Migration utilities for TiledViz database
Handles automatic migration of project owners from projects.id_users to project_members
"""

import logging
from sqlalchemy import text
from app import db
import app.models as models


def migrate_project_owners():
    """
    Migrate existing project owners from projects.id_users to project_members table.
    This function is idempotent - it can be run multiple times safely.
    """
    try:
        logging.info("Starting project owners migration...")
        
        # Check if migration is needed - projects with id_users but no owner membership
        projects_without_members = db.session.execute(text("""
            SELECT p.id, p.id_users, p.name
            FROM projects p
            LEFT JOIN project_members pm ON p.id = pm.project_id AND pm.role_type = 'owner'
            WHERE p.id_users IS NOT NULL 
            AND pm.project_id IS NULL
        """)).fetchall()
        
        # Check for projects without any owner (id_users = NULL)
        projects_without_owners = db.session.execute(text("""
            SELECT p.id, p.name
            FROM projects p
            LEFT JOIN project_members pm ON p.id = pm.project_id AND pm.role_type = 'owner'
            WHERE p.id_users IS NULL 
            AND pm.project_id IS NULL
        """)).fetchall()
        
        total_projects_to_migrate = len(projects_without_members) + len(projects_without_owners)
        
        if total_projects_to_migrate == 0:
            logging.info("No projects need migration - all owners already migrated")
            return True
        
        logging.info(f"Found {len(projects_without_members)} projects with id_users to migrate")
        logging.info(f"Found {len(projects_without_owners)} projects without any owner")
        logging.info(f"Total projects to process: {total_projects_to_migrate}")
        
        migrated_count = 0
        orphaned_projects = []
        
        # Migrate projects with id_users
        for project_id, owner_id, project_name in projects_without_members:
            try:
                # Check if the owner user still exists
                owner_user = db.session.query(models.Users).filter_by(id=owner_id).first()
                if not owner_user:
                    logging.warning(f"Owner user {owner_id} not found for project {project_name} (ID: {project_id})")
                    orphaned_projects.append((project_id, project_name, f"User {owner_id} not found"))
                    continue
                
                # Create owner membership record
                owner_membership = models.ProjectMembers(
                    project_id=project_id,
                    user_id=owner_id,
                    role_type='owner',
                    id_users=owner_id,  # Keep for backward compatibility
                    id_projects=project_id  # Keep for backward compatibility
                )
                
                db.session.add(owner_membership)
                migrated_count += 1
                
                logging.info(f"Created owner membership for project '{project_name}' (ID: {project_id}) -> User '{owner_user.name}' (ID: {owner_id})")
                
            except Exception as e:
                logging.error(f"Error migrating project {project_id}: {str(e)}")
                orphaned_projects.append((project_id, project_name, str(e)))
                continue
        
        # Handle projects without any owner (id_users = NULL)
        for project_id, project_name in projects_without_owners:
            try:
                # Try to find the first admin user to assign as owner
                first_admin = db.session.query(models.Users).filter_by(is_admin=True).first()
                
                if first_admin:
                    # Assign first admin as owner
                    owner_membership = models.ProjectMembers(
                        project_id=project_id,
                        user_id=first_admin.id,
                        role_type='owner',
                        id_users=first_admin.id,
                        id_projects=project_id
                    )
                    
                    db.session.add(owner_membership)
                    migrated_count += 1
                    
                    # Update the project's id_users field
                    project = db.session.query(models.Projects).filter_by(id=project_id).first()
                    if project:
                        project.id_users = first_admin.id
                    
                    logging.info(f"Assigned admin '{first_admin.name}' as owner for orphaned project '{project_name}' (ID: {project_id})")
                else:
                    # No admin user found - mark as orphaned
                    orphaned_projects.append((project_id, project_name, "No admin user available"))
                    logging.warning(f"No admin user found to assign as owner for project '{project_name}' (ID: {project_id})")
                
            except Exception as e:
                logging.error(f"Error handling orphaned project {project_id}: {str(e)}")
                orphaned_projects.append((project_id, project_name, str(e)))
                continue
        
        # Commit all changes
        db.session.commit()
        logging.info(f"Successfully migrated {migrated_count} project owners")
        
        # Report orphaned projects
        if orphaned_projects:
            logging.warning(f"Found {len(orphaned_projects)} orphaned projects that could not be migrated:")
            for project_id, project_name, reason in orphaned_projects:
                logging.warning(f"  - Project '{project_name}' (ID: {project_id}): {reason}")
            logging.warning("These projects need manual intervention via the admin interface")
        
        return True
        
    except Exception as e:
        logging.error(f"Migration failed: {str(e)}")
        db.session.rollback()
        return False


def check_migration_status():
    """
    Check the current migration status and return statistics
    """
    try:
        # Count projects with id_users but no owner in project_members
        unmigrated = db.session.execute(text("""
            SELECT COUNT(*)
            FROM projects p
            LEFT JOIN project_members pm ON p.id = pm.project_id AND pm.role_type = 'owner'
            WHERE p.id_users IS NOT NULL 
            AND pm.project_id IS NULL
        """)).scalar()
        
        # Count total projects with owners
        total_with_owners = db.session.execute(text("""
            SELECT COUNT(*) FROM projects WHERE id_users IS NOT NULL
        """)).scalar()
        
        # Count migrated projects
        migrated = total_with_owners - unmigrated
        
        return {
            'total_projects_with_owners': total_with_owners,
            'migrated_projects': migrated,
            'unmigrated_projects': unmigrated,
            'migration_complete': unmigrated == 0
        }
        
    except Exception as e:
        logging.error(f"Error checking migration status: {str(e)}")
        return None


def rollback_migration():
    """
    Rollback migration by removing owner memberships created by migration.
    WARNING: This will remove ALL owner memberships, not just migrated ones.
    """
    try:
        logging.warning("Starting migration rollback...")
        
        # Count owner memberships
        owner_count = db.session.query(models.ProjectMembers).filter_by(role_type='owner').count()
        
        if owner_count == 0:
            logging.info("No owner memberships to rollback")
            return True
        
        # Remove all owner memberships
        db.session.query(models.ProjectMembers).filter_by(role_type='owner').delete()
        db.session.commit()
        
        logging.warning(f"Rolled back {owner_count} owner memberships")
        return True
        
    except Exception as e:
        logging.error(f"Rollback failed: {str(e)}")
        db.session.rollback()
        return False


def get_orphaned_projects():
    """
    Get list of projects that don't have any owner
    """
    try:
        # Projects with id_users but user doesn't exist
        projects_with_invalid_owner = db.session.execute(text("""
            SELECT p.id, p.name, p.id_users
            FROM projects p
            LEFT JOIN users u ON p.id_users = u.id
            WHERE p.id_users IS NOT NULL 
            AND u.id IS NULL
        """)).fetchall()
        
        # Projects without any owner (id_users = NULL)
        projects_without_owner = db.session.execute(text("""
            SELECT p.id, p.name
            FROM projects p
            LEFT JOIN project_members pm ON p.id = pm.project_id AND pm.role_type = 'owner'
            WHERE p.id_users IS NULL 
            AND pm.project_id IS NULL
        """)).fetchall()
        
        return {
            'invalid_owner': projects_with_invalid_owner,
            'no_owner': projects_without_owner,
            'total_orphaned': len(projects_with_invalid_owner) + len(projects_without_owner)
        }
        
    except Exception as e:
        logging.error(f"Error getting orphaned projects: {str(e)}")
        return None


def validate_migration():
    """
    Validate that migration was successful by checking data consistency
    """
    try:
        # Check for orphaned project_members (no corresponding project)
        orphaned_members = db.session.execute(text("""
            SELECT COUNT(*)
            FROM project_members pm
            LEFT JOIN projects p ON pm.project_id = p.id
            WHERE p.id IS NULL
        """)).scalar()
        
        # Check for projects with id_users but no owner membership
        projects_without_owner_membership = db.session.execute(text("""
            SELECT COUNT(*)
            FROM projects p
            LEFT JOIN project_members pm ON p.id = pm.project_id AND pm.role_type = 'owner'
            WHERE p.id_users IS NOT NULL 
            AND pm.project_id IS NULL
        """)).scalar()
        
        # Check for multiple owners of the same project
        multiple_owners = db.session.execute(text("""
            SELECT project_id, COUNT(*)
            FROM project_members
            WHERE role_type = 'owner'
            GROUP BY project_id
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        validation_result = {
            'orphaned_members': orphaned_members,
            'projects_without_owner_membership': projects_without_owner_membership,
            'projects_with_multiple_owners': len(multiple_owners),
            'multiple_owners_details': multiple_owners,
            'is_valid': orphaned_members == 0 and projects_without_owner_membership == 0 and len(multiple_owners) == 0
        }
        
        if validation_result['is_valid']:
            logging.info("Migration validation passed")
        else:
            logging.warning(f"Migration validation issues: {validation_result}")
        
        return validation_result
        
    except Exception as e:
        logging.error(f"Migration validation failed: {str(e)}")
        return None
