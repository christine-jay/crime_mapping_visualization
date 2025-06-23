# These are plain Python classes for structure and utility, not ORM models.

class User:
    def __init__(self, user_id, name, username, password, role, user_email, profile_picture=None):
        self.user_id = user_id
        self.name = name
        self.username = username
        self.password = password
        self.role = role
        self.user_email = user_email
        self.profile_picture = profile_picture

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user_id)

class CrimeReport:
    def __init__(self, report_id, barangay_name, type_of_place, date_reported, time_reported, date_committed, time_committed, offense, type_of_crime, classification_of_crime, victim, suspect, narrative, status, batch_id):
        self.report_id = report_id
        self.barangay_name = barangay_name
        self.type_of_place = type_of_place
        self.date_reported = date_reported
        self.time_reported = time_reported
        self.date_committed = date_committed
        self.time_committed = time_committed
        self.offense = offense
        self.type_of_crime = type_of_crime
        self.classification_of_crime = classification_of_crime
        self.victim = victim
        self.suspect = suspect
        self.narrative = narrative
        self.status = status
        self.batch_id = batch_id

class Barangay:
    def __init__(self, barangay_id, barangay_name, barangay_population, barangay_district):
        self.barangay_id = barangay_id
        self.barangay_name = barangay_name
        self.barangay_population = barangay_population
        self.barangay_district = barangay_district

class AuditLog:
    def __init__(self, log_id, user_id, action, table_affected, timestamp):
        self.log_id = log_id
        self.user_id = user_id
        self.action = action
        self.table_affected = table_affected
        self.timestamp = timestamp

class PasswordReset:
    def __init__(self, reset_id, user_id, reset_token, expiration_time, is_used, created_at):
        self.reset_id = reset_id
        self.user_id = user_id
        self.reset_token = reset_token
        self.expiration_time = expiration_time
        self.is_used = is_used
        self.created_at = created_at 