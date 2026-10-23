-- Executable SQLite reference schema. Every institutional foreign key carries university_id.
-- Production web access additionally requires authorization and database row security.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS universities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    timezone TEXT NOT NULL,
    profile_status TEXT NOT NULL CHECK(profile_status IN ('draft','verified'))
);
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    identity_subject TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS university_memberships (
    university_id TEXT NOT NULL REFERENCES universities(id),
    account_id TEXT NOT NULL REFERENCES accounts(id),
    role TEXT NOT NULL CHECK(role IN ('owner','administrator','scheduler','viewer')),
    PRIMARY KEY(university_id, account_id)
);
CREATE TABLE IF NOT EXISTS campuses (
    university_id TEXT NOT NULL REFERENCES universities(id), id TEXT NOT NULL,
    name TEXT NOT NULL, PRIMARY KEY(university_id,id)
);
CREATE TABLE IF NOT EXISTS buildings (
    university_id TEXT NOT NULL, id TEXT NOT NULL, campus_id TEXT NOT NULL,
    name TEXT NOT NULL, PRIMARY KEY(university_id,id),
    FOREIGN KEY(university_id,campus_id) REFERENCES campuses(university_id,id)
);
CREATE TABLE IF NOT EXISTS floors (
    university_id TEXT NOT NULL, id TEXT NOT NULL, building_id TEXT NOT NULL,
    label TEXT NOT NULL, PRIMARY KEY(university_id,id),
    FOREIGN KEY(university_id,building_id) REFERENCES buildings(university_id,id)
);
CREATE TABLE IF NOT EXISTS architecture_revisions (
    university_id TEXT NOT NULL REFERENCES universities(id), id TEXT NOT NULL,
    effective_from TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('draft','approved')),
    description TEXT NOT NULL, PRIMARY KEY(university_id,id),
    UNIQUE(university_id,effective_from)
);
CREATE TRIGGER IF NOT EXISTS approved_architecture_immutable
BEFORE UPDATE ON architecture_revisions WHEN OLD.status='approved' BEGIN
    SELECT RAISE(ABORT, 'approved architecture revisions are immutable');
END;
CREATE TABLE IF NOT EXISTS floorplans (
    university_id TEXT NOT NULL, id TEXT NOT NULL, floor_id TEXT NOT NULL,
    architecture_revision_id TEXT NOT NULL, asset_uri TEXT NOT NULL, sha256 TEXT NOT NULL,
    coordinate_system TEXT NOT NULL, units TEXT,
    PRIMARY KEY(university_id,id),
    FOREIGN KEY(university_id,floor_id) REFERENCES floors(university_id,id),
    FOREIGN KEY(university_id,architecture_revision_id) REFERENCES architecture_revisions(university_id,id)
);
CREATE TABLE IF NOT EXISTS spaces (
    university_id TEXT NOT NULL REFERENCES universities(id), id TEXT NOT NULL,
    canonical_code TEXT NOT NULL, PRIMARY KEY(university_id,id),
    UNIQUE(university_id,canonical_code)
);
CREATE TABLE IF NOT EXISTS space_versions (
    university_id TEXT NOT NULL, id TEXT NOT NULL, space_id TEXT NOT NULL,
    architecture_revision_id TEXT NOT NULL, floor_id TEXT,
    name TEXT NOT NULL, kind TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('open','closed','retired')),
    seated_capacity INTEGER CHECK(seated_capacity>=0),
    exam_capacity INTEGER CHECK(exam_capacity>=0),
    usable_workstations INTEGER CHECK(usable_workstations>=0),
    features_json TEXT NOT NULL DEFAULT '[]', geometry_json TEXT,
    reviewed_for_scheduling INTEGER NOT NULL DEFAULT 0 CHECK(reviewed_for_scheduling IN (0,1)),
    PRIMARY KEY(university_id,id), UNIQUE(university_id,id,space_id),
    UNIQUE(university_id,space_id,architecture_revision_id),
    FOREIGN KEY(university_id,space_id) REFERENCES spaces(university_id,id),
    FOREIGN KEY(university_id,floor_id) REFERENCES floors(university_id,id),
    FOREIGN KEY(university_id,architecture_revision_id) REFERENCES architecture_revisions(university_id,id)
);
-- Effective until the next approved revision for this space; older versions are immutable.
CREATE TRIGGER IF NOT EXISTS space_version_immutable
BEFORE UPDATE ON space_versions BEGIN
    SELECT RAISE(ABORT, 'append a space version instead of overwriting history');
END;
CREATE TABLE IF NOT EXISTS space_lineage (
    university_id TEXT NOT NULL, predecessor_id TEXT NOT NULL, successor_id TEXT NOT NULL,
    architecture_revision_id TEXT NOT NULL, relation TEXT NOT NULL CHECK(relation IN ('split','merged','replaced')),
    PRIMARY KEY(university_id,predecessor_id,successor_id,architecture_revision_id),
    CHECK(predecessor_id<>successor_id),
    FOREIGN KEY(university_id,predecessor_id) REFERENCES spaces(university_id,id),
    FOREIGN KEY(university_id,successor_id) REFERENCES spaces(university_id,id),
    FOREIGN KEY(university_id,architecture_revision_id) REFERENCES architecture_revisions(university_id,id)
);
CREATE TABLE IF NOT EXISTS physical_resource_atoms (
    university_id TEXT NOT NULL REFERENCES universities(id), id TEXT NOT NULL,
    description TEXT NOT NULL, PRIMARY KEY(university_id,id)
);
CREATE TABLE IF NOT EXISTS space_occupancy_atoms (
    university_id TEXT NOT NULL, space_version_id TEXT NOT NULL, atom_id TEXT NOT NULL,
    PRIMARY KEY(university_id,space_version_id,atom_id),
    FOREIGN KEY(university_id,space_version_id) REFERENCES space_versions(university_id,id),
    FOREIGN KEY(university_id,atom_id) REFERENCES physical_resource_atoms(university_id,id)
);
CREATE TABLE IF NOT EXISTS space_aliases (
    university_id TEXT NOT NULL, space_id TEXT NOT NULL, context_key TEXT NOT NULL,
    alias TEXT NOT NULL, PRIMARY KEY(university_id,context_key,alias),
    FOREIGN KEY(university_id,space_id) REFERENCES spaces(university_id,id)
);
CREATE TABLE IF NOT EXISTS navigation_nodes (
    university_id TEXT NOT NULL, id TEXT NOT NULL, architecture_revision_id TEXT NOT NULL,
    floor_id TEXT, space_id TEXT, kind TEXT NOT NULL,
    PRIMARY KEY(university_id,id), UNIQUE(university_id,id,architecture_revision_id),
    FOREIGN KEY(university_id,architecture_revision_id) REFERENCES architecture_revisions(university_id,id),
    FOREIGN KEY(university_id,floor_id) REFERENCES floors(university_id,id),
    FOREIGN KEY(university_id,space_id) REFERENCES spaces(university_id,id)
);
CREATE TABLE IF NOT EXISTS navigation_edges (
    university_id TEXT NOT NULL, from_node_id TEXT NOT NULL, to_node_id TEXT NOT NULL,
    architecture_revision_id TEXT NOT NULL,
    profile TEXT NOT NULL, travel_seconds INTEGER NOT NULL CHECK(travel_seconds>=0),
    PRIMARY KEY(university_id,from_node_id,to_node_id,profile),
    FOREIGN KEY(university_id,from_node_id,architecture_revision_id) REFERENCES navigation_nodes(university_id,id,architecture_revision_id),
    FOREIGN KEY(university_id,to_node_id,architecture_revision_id) REFERENCES navigation_nodes(university_id,id,architecture_revision_id)
);
-- Dated availability is expanded from approved recurring opening rules and overrides.
CREATE TABLE IF NOT EXISTS availability_intervals (
    university_id TEXT NOT NULL, id TEXT NOT NULL, space_id TEXT NOT NULL,
    starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('open','blocked')), reason TEXT NOT NULL,
    PRIMARY KEY(university_id,id), CHECK(ends_at>starts_at),
    FOREIGN KEY(university_id,space_id) REFERENCES spaces(university_id,id)
);
CREATE TABLE IF NOT EXISTS terms (
    university_id TEXT NOT NULL REFERENCES universities(id), id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('first','second','summer')),
    starts_on TEXT NOT NULL, ends_on TEXT NOT NULL, calendar_json TEXT NOT NULL,
    PRIMARY KEY(university_id,id), CHECK(ends_on>starts_on)
);
CREATE TABLE IF NOT EXISTS offerings (
    university_id TEXT NOT NULL, id TEXT NOT NULL, term_id TEXT NOT NULL,
    course_code TEXT NOT NULL, regulation_version TEXT NOT NULL,
    required_components_json TEXT NOT NULL,
    PRIMARY KEY(university_id,id),
    FOREIGN KEY(university_id,term_id) REFERENCES terms(university_id,id)
);
CREATE TABLE IF NOT EXISTS students (
    university_id TEXT NOT NULL REFERENCES universities(id), student_key TEXT NOT NULL,
    mobility_profile TEXT NOT NULL DEFAULT 'standard', PRIMARY KEY(university_id,student_key)
);
CREATE TABLE IF NOT EXISTS enrolments (
    university_id TEXT NOT NULL, student_key TEXT NOT NULL, offering_id TEXT NOT NULL,
    PRIMARY KEY(university_id,student_key,offering_id),
    FOREIGN KEY(university_id,student_key) REFERENCES students(university_id,student_key),
    FOREIGN KEY(university_id,offering_id) REFERENCES offerings(university_id,id)
);
CREATE TABLE IF NOT EXISTS component_assignments (
    university_id TEXT NOT NULL, student_key TEXT NOT NULL, offering_id TEXT NOT NULL,
    component TEXT NOT NULL, section_key TEXT NOT NULL,
    PRIMARY KEY(university_id,student_key,offering_id,component),
    FOREIGN KEY(university_id,student_key,offering_id) REFERENCES enrolments(university_id,student_key,offering_id)
);
CREATE TABLE IF NOT EXISTS staff (
    university_id TEXT NOT NULL REFERENCES universities(id), id TEXT NOT NULL,
    roles_json TEXT NOT NULL, availability_json TEXT NOT NULL,
    PRIMARY KEY(university_id,id)
);
CREATE TABLE IF NOT EXISTS assessments (
    university_id TEXT NOT NULL, id TEXT NOT NULL, offering_id TEXT NOT NULL,
    kind TEXT NOT NULL, requirements_json TEXT NOT NULL,
    PRIMARY KEY(university_id,id), UNIQUE(university_id,id,offering_id),
    FOREIGN KEY(university_id,offering_id) REFERENCES offerings(university_id,id)
);
CREATE TABLE IF NOT EXISTS event_occurrences (
    university_id TEXT NOT NULL, id TEXT NOT NULL, offering_id TEXT NOT NULL,
    activity_kind TEXT NOT NULL, assessment_key TEXT, section_key TEXT,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes>0),
    requirements_json TEXT NOT NULL,
    PRIMARY KEY(university_id,id), UNIQUE(university_id,id,offering_id), UNIQUE(university_id,id,assessment_key),
    FOREIGN KEY(university_id,offering_id) REFERENCES offerings(university_id,id),
    FOREIGN KEY(university_id,assessment_key,offering_id) REFERENCES assessments(university_id,id,offering_id)
);
CREATE TABLE IF NOT EXISTS event_participants (
    university_id TEXT NOT NULL, event_id TEXT NOT NULL, student_key TEXT NOT NULL, offering_id TEXT NOT NULL,
    PRIMARY KEY(university_id,event_id,student_key),
    FOREIGN KEY(university_id,event_id,offering_id) REFERENCES event_occurrences(university_id,id,offering_id),
    FOREIGN KEY(university_id,student_key,offering_id) REFERENCES enrolments(university_id,student_key,offering_id)
);
CREATE TABLE IF NOT EXISTS event_staff (
    university_id TEXT NOT NULL, event_id TEXT NOT NULL, staff_id TEXT NOT NULL, role TEXT NOT NULL,
    PRIMARY KEY(university_id,event_id,staff_id,role),
    FOREIGN KEY(university_id,event_id) REFERENCES event_occurrences(university_id,id),
    FOREIGN KEY(university_id,staff_id) REFERENCES staff(university_id,id)
);
CREATE TABLE IF NOT EXISTS assessment_sitting_assignments (
    university_id TEXT NOT NULL, student_key TEXT NOT NULL, assessment_id TEXT NOT NULL, event_id TEXT NOT NULL,
    PRIMARY KEY(university_id,student_key,assessment_id),
    FOREIGN KEY(university_id,assessment_id) REFERENCES assessments(university_id,id),
    FOREIGN KEY(university_id,event_id,assessment_id) REFERENCES event_occurrences(university_id,id,assessment_key),
    FOREIGN KEY(university_id,event_id,student_key) REFERENCES event_participants(university_id,event_id,student_key)
);
CREATE TABLE IF NOT EXISTS source_documents (
    university_id TEXT NOT NULL REFERENCES universities(id), id TEXT NOT NULL,
    origin_key TEXT NOT NULL, source_uri TEXT NOT NULL, sha256 TEXT, scan_metadata_json TEXT NOT NULL,
    PRIMARY KEY(university_id,id)
);
CREATE TABLE IF NOT EXISTS import_candidates (
    university_id TEXT NOT NULL REFERENCES universities(id), id TEXT NOT NULL,
    label TEXT NOT NULL, proposed_kind TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending_review','approved','rejected')),
    confirmed_space_id TEXT, PRIMARY KEY(university_id,id),
    CHECK(status<>'approved' OR confirmed_space_id IS NOT NULL),
    FOREIGN KEY(university_id,confirmed_space_id) REFERENCES spaces(university_id,id)
);
CREATE TABLE IF NOT EXISTS import_observations (
    university_id TEXT NOT NULL, id TEXT NOT NULL,
    candidate_id TEXT NOT NULL, source_id TEXT NOT NULL, page INTEGER NOT NULL CHECK(page>0),
    extraction_method TEXT NOT NULL, bbox_json TEXT NOT NULL,
    PRIMARY KEY(university_id,id),
    FOREIGN KEY(university_id,candidate_id) REFERENCES import_candidates(university_id,id),
    FOREIGN KEY(university_id,source_id) REFERENCES source_documents(university_id,id)
);
CREATE TABLE IF NOT EXISTS solver_runs (
    university_id TEXT NOT NULL REFERENCES universities(id), id TEXT NOT NULL,
    input_sha256 TEXT NOT NULL, input_snapshot_uri TEXT NOT NULL,
    solver_version TEXT NOT NULL, settings_json TEXT NOT NULL, status TEXT NOT NULL,
    PRIMARY KEY(university_id,id)
);
CREATE TABLE IF NOT EXISTS schedule_assignments (
    university_id TEXT NOT NULL, run_id TEXT NOT NULL, event_id TEXT NOT NULL,
    starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
    PRIMARY KEY(university_id,run_id,event_id), CHECK(ends_at>starts_at),
    FOREIGN KEY(university_id,run_id) REFERENCES solver_runs(university_id,id),
    FOREIGN KEY(university_id,event_id) REFERENCES event_occurrences(university_id,id)
);
CREATE TABLE IF NOT EXISTS assignment_spaces (
    university_id TEXT NOT NULL, run_id TEXT NOT NULL, event_id TEXT NOT NULL,
    space_id TEXT NOT NULL, space_version_id TEXT NOT NULL,
    PRIMARY KEY(university_id,run_id,event_id,space_id),
    FOREIGN KEY(university_id,run_id,event_id) REFERENCES schedule_assignments(university_id,run_id,event_id),
    FOREIGN KEY(university_id,space_version_id,space_id) REFERENCES space_versions(university_id,id,space_id)
);
CREATE INDEX IF NOT EXISTS enrolment_by_offering ON enrolments(university_id,offering_id,student_key);
CREATE INDEX IF NOT EXISTS participants_by_student ON event_participants(university_id,student_key,event_id);
CREATE INDEX IF NOT EXISTS observation_by_source ON import_observations(university_id,source_id,page);
