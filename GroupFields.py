from datetime import datetime

GROUP_NAME = "Group Name"
FULL_GROUP_NAME = "Full Group Name"
GROUP_DIR = "Group Dir"
GROUP_TYPE = "Group Type"
Q4_PATH = "Q4 Path"
Q4_FILENAME = "Q4 Filename"
Q1_PATH = "Q1 Path"
Q1_STATUS = "Q1 Status"
BRANCH = "Branch"
NOTE = "Note"
REGION = "Region"
STATE = "State"
fields = [GROUP_NAME, FULL_GROUP_NAME, GROUP_DIR, GROUP_TYPE, Q4_PATH, Q4_FILENAME,
          Q1_PATH, Q1_STATUS, BRANCH, NOTE, REGION, STATE]

OTHER = "Other"
PREFIX = "STARTING "
THIS_YEAR = datetime.now().year
THIS_YEAR_DIR = f"\\{THIS_YEAR}\\"
QUARTERLY_REPORTS = "Quarterly Reports"
THIS_YEAR_QUARTERLY_REPORTS = f"{THIS_YEAR_DIR}{QUARTERLY_REPORTS}"
THIS_YEAR_PREFIX = f"{PREFIX}{THIS_YEAR} Q1 "
LAST_YEAR = datetime.now().year - 1
LAST_YEAR_DIR = f"\\{LAST_YEAR}\\"


# class GroupFields:
#
#     def __init__(self):
#         self.group_names = {} # fields
#
#     def set_field(self, group_name, field_name, field_value):
#         self.group_names[group_name][field_name] = field_value
#
#     def get_field(self, group_name, field_name):
#         return self.group_names[group_name][field_name]
#


def get_q1_path_from_q4_file_path(q4_file_path):
    q1_path = q4_file_path.partition(f"{LAST_YEAR_DIR}")[0]
    q1_path = f"{q1_path}{THIS_YEAR_DIR}{QUARTERLY_REPORTS}\\"
    return q1_path


def get_this_year_path_from_group_path(group_path):
    this_year_path = f"{group_path}{THIS_YEAR_PREFIX}"
    return this_year_path
