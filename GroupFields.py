from datetime import datetime

import Persistence

UNKNOWN = "Unknown"
RESOURCES = "Resources"
TEST = "Test"
OTHER = "Other"
ALL = "All"
READ_FROM_FILE_NAMES = [RESOURCES, TEST]


GROUP_NAME = "Group Name"
FULL_GROUP_NAME = "Full Group Name"
GROUP_DIR = "Group Dir"
GROUP_TYPE = "Group Type"
Q4_PATH = "Q4 Path"
Q4_FILENAME = "Q4 Filename"
Q1_PATH = "Q1 Path"
Q1_STEM = "Q1 Stem"
Q1_STATUS = "Q1 Status"
BRANCH = "Branch"
NOTE = "Note"
LOCATION = "Location"
E_REGION = "Exchequer Region"
STATE = "State"
NUM_ACCOUNTS = "Number of Accounts"
fields = [GROUP_NAME, FULL_GROUP_NAME, GROUP_DIR, GROUP_TYPE, Q4_PATH, Q4_FILENAME,
          Q1_PATH, Q1_STEM, Q1_STATUS, BRANCH, NOTE, E_REGION, STATE, LOCATION, NUM_ACCOUNTS]

OTHER = "Other"
RESOURCES = "Resources"
CORPORATE = "Corporate"
PREFIX = "STARTING "
THIS_YEAR = datetime.now().year
THIS_YEAR_DIR = f"\\{THIS_YEAR}\\"
QUARTERLY_REPORTS = "Quarterly Reports"
THIS_YEAR_QUARTERLY_REPORTS = f"{THIS_YEAR_DIR}{QUARTERLY_REPORTS}"
THIS_YEAR_PREFIX = f"{PREFIX}{THIS_YEAR} Q1 "
LAST_YEAR = datetime.now().year - 1
LAST_YEAR_DIR = f"\\{LAST_YEAR}\\"


def get_field(fields, field_name):
    if field_name not in fields:
        return None
    return fields[field_name]

def get_q1_path_from_q4_file_path(q4_file_path):
    q1_path = q4_file_path.partition(f"{LAST_YEAR_DIR}")[0]
    q1_path = f"{q1_path}{THIS_YEAR_DIR}{QUARTERLY_REPORTS}\\"
    return q1_path

def get_this_year_path_from_group_path(group_path):
    this_year_path = f"{group_path}{THIS_YEAR_PREFIX}"
    return this_year_path


class GroupFields:
    group_names = {}  # fields
    substitutions = Persistence.get_dict("Group_Substitutions.csv", Persistence.RESOURCE_PATH)
    group_data = Persistence.get_dict("SCA Regions.csv", Persistence.RESOURCE_PATH, False)

    def __init__(self):
        pass

    @classmethod
    def set_group_field(cls, group_name, field_name, field_value):
        cls.group_names[group_name][field_name] = field_value

    @classmethod
    def get_group_field(cls, group_name, field_name):
        return get_field(cls.group_names[group_name], [field_name])

    @classmethod
    def lookup_group_fields(cls, name_of_branch, group_path, group_name_fields):
        group_name_data = []
        group_name = Persistence.remove_surrounding_parens(name_of_branch)
        if "," in group_name:
            group_name = group_name.split(",")[1].strip()  # remove things like "SCA Inc., "
        if group_name_fields == {}:
            group_name_fields[FULL_GROUP_NAME] = name_of_branch
            if group_name == OTHER:
                group_name_fields[BRANCH] = group_name
            else:
                group_name_fields[BRANCH] = group_path.split("\\")[2]
            group_name_fields[GROUP_TYPE] = None
        try:
            group_name_data = cls.group_data[group_name]
        except KeyError as e:
            if GROUP_DIR in group_name_fields:
                try:
                    group_dir = group_name_fields[GROUP_DIR]
                    group_name = group_dir.split("\\")[-1]
                    group_name = Persistence.remove_surrounding_parens(group_name)
                    group_name_data = cls.group_data[group_name]
                except KeyError as e:
                    group_name_fields[NOTE] = UNKNOWN
                    return group_name, group_name_fields

        if group_name_data:
            if group_name != OTHER:
                group_name_fields[FULL_GROUP_NAME] = group_name_data[0]
                group_name_fields[BRANCH] = group_name_data[3]
                group_name_fields[GROUP_TYPE] = group_name_data[1]
            group_name_fields[LOCATION] = group_name_data[2]
            group_name_fields[NOTE] = group_name_data[4]
            group_name_fields[E_REGION] = group_name_data[5]

        return group_name, group_name_fields

    @classmethod
    def lookup_full_group_name(cls, group_name):
        try:
            full_group_name = cls.group_data[group_name]
            return full_group_name[0]
        except KeyError:
            return None

    @classmethod
    def substitute_group_name(cls, name_of_branch):
        group_name = Persistence.remove_surrounding_parens(name_of_branch)
        try:
            group_name = cls.substitutions[group_name]
        except KeyError:
            pass
        return group_name
