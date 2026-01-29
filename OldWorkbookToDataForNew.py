'''
OldWorkbookToNew.py uses openpyxl which has a problem saving files
UserWarning: Conditional Formatting extension is not supported and will be removed
UserWarning: Data Validation extension is not supported and will be removed

the new strategy is to use it to gather the data, but not to save the new file
we will need to write a macro to load the data and save the file, then delete the data file
This reading of the data file and saving may have to be executed for each file manually
'''
from datetime import datetime
from os.path import exists

import openpyxl

import Persistence

VERIFY_DATA_ONLY = False

class OldWorkbookToDataForNew:
    GROUP_TYPES = ["Barony", "Canton", "City", "College", "Event", "Kingdom", "Port", "Principality",
                   "Project/Newsletter", "Province", "Shire", "Sub Account"]
    KINGDOM = "East Kingdom"
    BANK_ACCOUNT_TYPE_CHOICES = ["Checking", "Savings", "CD/GIC", "Money Market"]
    SIGNATORY_CHOICES = ["Single", "Dual"]
    INTEREST_BEARING_CHOICES = ["Yes", "No"]

    def __init__(self, old_workbook_file_path,
                 output_file_path,
                 master_data_file_path="Resources\\SCA Exchequer Report - 2026-02.xlsx",
                 ):
        self.old_workbook_file_path = old_workbook_file_path
        self.master_data_file_path = master_data_file_path
        self.output_file_path = output_file_path
        self.old_workbook = openpyxl.load_workbook(self.old_workbook_file_path, data_only=True)
        self.state = None
        self.new_data = []
        self.append_data("Sheet", "Coord", "Value", "Locked")

    def append_data(self, worksheet_name, cell_name, value, locked=False):
        if value:
            self.new_data.append([worksheet_name, cell_name, value, locked])

    def save_notes(self):
        self.append_data("Notes", "A1", self.state)
        self.append_data("Notes", "B1", self.output_file_path)

    def save_summary(self):
        ws_old_contents = self.old_workbook["Contents"]
        name_of_branch = ws_old_contents["C8"].value
        print(f"Branch name = {name_of_branch}")
        self.name_of_branch, group_type = self.lookup_group_name_type(name_of_branch)
        self.append_data("Summary", "D6", group_type)
        self.append_data("Summary", "D7", self.KINGDOM)
        state = ws_old_contents["C15"].value
        self.state = state
        self.append_data("Summary", "D8", state)
        self.append_data("Summary", "D9", name_of_branch)
        currency = ws_old_contents["C14"].value
        self.append_data("Summary", "H8", currency)

    def save_exchequer(self):
        ws_old_contents = self.old_workbook["Contents"]
        exchequer_name = ws_old_contents["C10"].value
        self.append_data("Exchequers", "C8", exchequer_name)
        ws_old_contact_info = self.old_workbook["CONTACT_INFO_1"]
        sca_name = ws_old_contact_info["D16"].value
        self.append_data("Exchequers", "C9", sca_name)
        membership_no = ws_old_contact_info["H15"].value
        self.append_data("Exchequers", "L8", membership_no)
        expiration_date = self.dmy(ws_old_contact_info["H16"].value)
        self.append_data("Exchequers", "L9", expiration_date)
        home_address = ws_old_contact_info["D12"].value
        self.append_data("Exchequers", "D10", home_address)
        city_town = ws_old_contact_info["D13"].value
        self.append_data("Exchequers", "K10", city_town)
        state_or_province = ws_old_contact_info["F13"].value
        self.append_data("Exchequers", "C11", state_or_province)
        zip_code = ws_old_contact_info["H13"].value
        self.append_data("Exchequers", "G11", zip_code)
        home_phone = ws_old_contact_info["D14"].value
        alt_phone = ws_old_contact_info["F14"].value
        phone = self.get_phone(alt_phone, home_phone)
        self.append_data("Exchequers", "C12", phone)
        personal_email = ws_old_contact_info["D15"].value
        self.append_data("Exchequers", "H12", personal_email)

    def get_phone(self, home_phone, alt_phone):
        if alt_phone and home_phone:
            return home_phone + ", " + alt_phone
        else:
            return home_phone

    def save_deputy_exchequer_1(self):
        ws_old_contact_info = self.old_workbook["CONTACT_INFO_1"]
        deputy_exchequer_name = ws_old_contact_info["D22"].value
        self.append_data("Exchequers", "C16", deputy_exchequer_name)
        deputy_sca_name = ws_old_contact_info["D27"].value
        self.append_data("Exchequers", "C17", deputy_sca_name)
        membership_no = ws_old_contact_info["H26"].value
        self.append_data("Exchequers", "L16", membership_no)
        expiration_date = self.dmy(ws_old_contact_info["H27"].value)
        self.append_data("Exchequers", "L17", expiration_date)
        home_address = ws_old_contact_info["D23"].value
        self.append_data("Exchequers", "D18", home_address)
        city_town = ws_old_contact_info["D24"].value
        self.append_data("Exchequers", "K18", city_town)
        state_or_province = ws_old_contact_info["F24"].value
        self.append_data("Exchequers", "C19", state_or_province)
        zip_code = ws_old_contact_info["H24"].value
        self.append_data("Exchequers", "G19", zip_code)
        home_phone = ws_old_contact_info["D25"].value
        alt_phone = ws_old_contact_info["F25"].value
        phone = self.get_phone(home_phone, alt_phone)
        self.append_data("Exchequers", "C20", phone)
        personal_email = ws_old_contact_info["D26"].value
        self.append_data("Exchequers", "H20", personal_email)

    def save_deputy_exchequer_2(self):
        ws_old_contact_info = self.old_workbook["CONTACT_INFO_1"]
        deputy_exchequer_name = ws_old_contact_info["D30"].value
        self.append_data("Exchequers", "C24", deputy_exchequer_name)
        sca_name = ws_old_contact_info["D35"].value
        self.append_data("Exchequers", "C25", sca_name)
        membership_no = ws_old_contact_info["H34"].value
        self.append_data("Exchequers", "L24", membership_no)
        expiration_date = self.dmy(ws_old_contact_info["H35"].value)
        self.append_data("Exchequers", "L25", expiration_date)
        home_address = ws_old_contact_info["D31"].value
        self.append_data("Exchequers", "D26", home_address)
        city_town = ws_old_contact_info["D32"].value
        self.append_data("Exchequers", "K26", city_town)
        state_or_province = ws_old_contact_info["F32"].value
        self.append_data("Exchequers", "C27", state_or_province)
        zip_code = ws_old_contact_info["H32"].value
        self.append_data("Exchequers", "G27", zip_code)
        home_phone = ws_old_contact_info["D33"].value
        alt_phone = ws_old_contact_info["F33"].value
        phone = self.get_phone(home_phone, alt_phone)
        self.append_data("Exchequers", "C28", phone)
        personal_email = ws_old_contact_info["D34"].value
        self.append_data("Exchequers", "H28", personal_email)

    def save_financial_committee(self):

        ws_old_contents = self.old_workbook["Contents"]
        seneshal_name = ws_old_contents["C9"].value
        self.append_data("FinancialCommittee", "C11", seneshal_name)
        ws_old_financial_committee = self.old_workbook["FINANCE_COMM_13"]
        # add Choices 2 or 3
        choice_2 = ws_old_financial_committee["C12"].value
        choice_3 = ws_old_financial_committee["C13"].value
        if choice_2:
            choice = 2
        else:
            choice = 3

        seneshal_sca_name = ws_old_financial_committee["D18"].value
        self.append_data("FinancialCommittee", "C12", seneshal_sca_name)
        seneshal_member_number = ws_old_financial_committee["E17"].value
        self.append_data("FinancialCommittee", "D11", seneshal_member_number)
        seneshal_expiry_date = self.dmy(ws_old_financial_committee["F17"].value)
        self.append_data("FinancialCommittee", "E11", seneshal_expiry_date)

        if choice == 3:
            for i in range(17):
                old_row = 21+i*2
                modern_name = ws_old_financial_committee[f"D{old_row}"].value
                if not modern_name:
                    break
                title = ws_old_financial_committee[f"C{old_row}"].value
                sca_name = ws_old_financial_committee[f"D{old_row+1}"].value
                membership_no = ws_old_financial_committee[f"E{old_row}"].value
                expiration_date = self.dmy(ws_old_financial_committee[f"F{old_row}"].value)

                self.append_data("FinancialCommittee", f"B{i*2+15}", title)
                self.append_data("FinancialCommittee", f"C{i*2+15}", modern_name)
                self.append_data("FinancialCommittee", f"C{i*2+16}", sca_name)
                self.append_data("FinancialCommittee", f"D{i*2+15}", membership_no)
                self.append_data("FinancialCommittee", f"E{i*2+15}", expiration_date)

    def save_primary_account(self):
        ws_old_primary_account = self.old_workbook["PRIMARY_ACCOUNT_2a"]
        bank_name = ws_old_primary_account["E13"].value
        self.append_data("Accounts", "B9", bank_name)
        bank_account_title = ws_old_primary_account["E14"].value
        self.append_data("Accounts", "B8", bank_account_title)
        bank_contact = ws_old_primary_account["F17"].value
        self.append_data("Accounts", "B10", bank_contact)
        bank_account_type = ws_old_primary_account["E15"].value
        choice = self.get_choice(self.BANK_ACCOUNT_TYPE_CHOICES, bank_account_type)
        self.append_data("Accounts", "B12", choice)

        signature_requirement = ws_old_primary_account["H15"].value
        choice = self.get_choice(self.SIGNATORY_CHOICES, signature_requirement)
        self.append_data("Accounts", "B13", choice)

        bank_account_number = ws_old_primary_account["E16"].value
        self.append_data("Accounts", "B11", bank_account_number)
        balance = ws_old_primary_account["H19"].value
        self.append_data("Accounts", "C16", balance, True)
        ledger_balance = ws_old_primary_account["H37"].value
        self.append_data("Accounts", "C17", ledger_balance, True)
        interest_bearing = ws_old_primary_account["F38"].value
        choice = self.get_choice(self.INTEREST_BEARING_CHOICES, interest_bearing)
        self.append_data("Accounts", "B14", choice)


        # signatories
        for i in range(6):
            old_row = 42 + i * 2
            signatory_name = ws_old_primary_account[f"E{old_row}"].value
            if not signatory_name:
                break
            signatory_member_number = ws_old_primary_account[f"H{old_row}"].value
            signatory_expiry_date = self.dmy(ws_old_primary_account[f"H{old_row + 1}"].value)

            new_row = 16 + i
            new_cols = "EIJ"
            if i>=4:
                new_row -= 4
                new_cols = "LPQ"
            self.append_data("Accounts", f"{new_cols[0]}{new_row}", signatory_name)
            self.append_data("Accounts", f"{new_cols[1]}{new_row}", signatory_member_number)
            self.append_data("Accounts", f"{new_cols[2]}{new_row}", signatory_expiry_date)

    def save_secondary_accounts(self):
        """Missing Contact info and SCA Name on Account"""
        ws_old_secondary_account = self.old_workbook["SECONDARY_ACCOUNTS_2b"]
        old_cols = "DEFG"
        for account in range(4):
            col = old_cols[account]
            new_summary_row = 20
            new_row_start = account*15+22
            bank_name = ws_old_secondary_account[f"{col}13"].value
            if bank_name is None:
                return

            self.append_data("Accounts", f"B{new_row_start+2}", bank_name)
            bank_account_type = ws_old_secondary_account[f"{col}16"].value
            choice = self.get_choice(self.BANK_ACCOUNT_TYPE_CHOICES, bank_account_type)
            bank_account_title = f"{bank_name}, {choice}"
            self.append_data("Summary", f"B{new_summary_row+account}", bank_account_title)
            self.append_data("Accounts", f"B{new_row_start+5}", choice)

            signature_requirement = ws_old_secondary_account[f"{col}15"].value
            choice = self.get_choice(self.SIGNATORY_CHOICES, signature_requirement)
            self.append_data("Accounts", f"{col}28", choice)

            self.append_data("Summary", "B20", bank_account_type)
            bank_account_number = ws_old_secondary_account[f"{col}14"].value
            self.append_data("Accounts", "B26", bank_account_number)
            balance = ws_old_secondary_account[f"{col}19"].value
            self.append_data("Accounts", "C31", balance, True)
            ledger_balance = ws_old_secondary_account["D25"].value
            self.append_data("Accounts", "C32", ledger_balance, True)

            interest_bearing = ws_old_secondary_account[f"{col}17"].value
            choice = self.get_choice(self.INTEREST_BEARING_CHOICES, interest_bearing)
            self.append_data("Accounts", "B29", choice)

            # signatories
            for i in range(6):
                old_row = 42 + i * 2
                signatory_name = ws_old_secondary_account[f"E{old_row}"].value
                if not signatory_name:
                    break
                signatory_member_number = ws_old_secondary_account[f"H{old_row}"].value
                signatory_expiry_date = self.dmy(ws_old_secondary_account[f"H{old_row + 1}"].value)

                new_row = 16 + i
                new_cols = "EIJ"
                if i >= 4:
                    new_row -= 4
                    new_cols = "LPQ"
                self.append_data("Accounts", f"{new_cols[0]}{new_row}", signatory_name)
                self.append_data("Accounts", f"{new_cols[1]}{new_row}", signatory_member_number)
                self.append_data("Accounts", f"{new_cols[2]}{new_row}", signatory_expiry_date)

    def set_bank_account_type(self, cell, bank_account_type):
        choices = ["Checking", "Savings", "CD/GIC", "Money Market"]
        choice = self.get_choice(choices, bank_account_type)
        self.append_data("Accounts", cell, choice)

    def save_funds(self):
        ws_old_funds = self.old_workbook["FUNDS_14"]
        # TODO from

    def save_outstanding(self):
        # TODO PRIMARY_ACCOUNT_2a 1. Balance from bank statement at end of period (6 of them)
        # and 16 possible checks
        # ASSET_DTL_5a undeposited funds... (6 of them)
        pass

    def save_liabilities(self):
        # TODO from LIABILITY_DTL_5b
        pass

    def save_assets(self):
        # TODO from ASSET_DTL_5a
        pass

    def get_choice(self, choices, value):
        if value is None:
            return None
        for choice in choices:
            if choice.lower() == value.lower():
                return choice
            elif value.lower() == choice.lower()[0:len(value)]:  # permit "Saving" to match "Savings"
                return choice
            elif choice.lower() == value.lower()[0:len(choice)]:  # permit "Dual Signature" to match "Dual"
                return choice
            elif choice.lower() in value.lower():
                return choice
        print(f"Invalid choice: {value}")
        return value

    def save_data(self):
        new_data_file_name = self.get_new_data_file_name()
        new_q1_file_path = f"{self.output_file_path}\\{new_data_file_name}.xlsx"
        if exists(new_q1_file_path):
            print(f"File {new_q1_file_path} already exists")
            return

        lines = []
        for data in self.new_data:
            lines.append(f'"{data[0]}","{data[1]}","{data[2]}","{data[3]}"')

        new_data_file_name = self.get_new_data_file_name()
        new_data_file_path = f"{self.output_file_path}\\{new_data_file_name}.csv"
        Persistence.write_lines(new_data_file_path, lines, path_type=Persistence.FILE_PATH)

    def get_new_data_file_name(self) -> str:
        current_year = datetime.now().year
        new_data_file_name = f"{current_year} Q1 {self.name_of_branch}"
        return new_data_file_name

    def save_new_data(self):
        self.save_notes()
        self.save_summary()
        self.save_exchequer()
        self.save_deputy_exchequer_1()
        self.save_deputy_exchequer_2()
        self.save_financial_committee()
        self.save_primary_account()
        self.save_secondary_accounts()
        self.save_funds()
        self.save_liabilities()
        self.save_outstanding()
        self.save_assets()
        self.save_data()

    def save_new_workbook(self):
        self.new_workbook = openpyxl.load_workbook(self.master_data_file_path)
        first = True
        for new_data in self.new_data:
            if first:
                first = False
                continue
            self.set_new_data(new_data)

        new_data_file_name = self.get_new_data_file_name()
        new_data_file_path = f"Resources\\{new_data_file_name}.xlsx"
        self.new_workbook.save(new_data_file_path)

    @staticmethod
    def dmy(dt):
        if not dt:
            return None
        if type(dt) == str:
            return dt.replace(" ", "")
        dmy = dt.strftime("%m/%d/%Y")
        return dmy

    def set_new_data(self, new_data):
        print(new_data)
        ws = self.new_workbook[new_data[0]]
        cell_obj = ws[new_data[1]]
        cell_obj.value = new_data[2]

    def lookup_group_name_type(self, name_of_branch):
        group_name = name_of_branch
        group_type = None
        lines = Persistence.get_lines("SCA Regions.csv", Persistence.RESOURCE_PATH)
        for line in lines:
            csv = line.split(",")
            group_name = csv[1].strip()
            if group_name and group_name.lower() in name_of_branch.lower():
                group_type = csv[0].strip()
                if group_type not in self.GROUP_TYPES:
                    group_type = csv[4].strip()
                break
        return group_name, group_type

def main():
    # TODO state from google drive if missing
    wbs = OldWorkbookToDataForNew("Resources\\2025 Q4 EK-Quarterly-Report_Carolingia updated by Kex.xlsm",
                                  "Resources\\2026 Q1 Barony of Carolingia.xlsm")
    wbs.save_new_data()
    if VERIFY_DATA_ONLY:
        wbs.save_new_workbook()

    wbs = OldWorkbookToDataForNew("Resources\\EK-Towers 2025-Q4.xlsm",
                                  "Resources\\EK-Towers 2025-Q4.xlsm")
    wbs.save_new_data()
    if VERIFY_DATA_ONLY:
        wbs.save_new_workbook()

    # TODO fix data validation https://openpyxl.readthedocs.io/en/3.1/validation.html
    # FinancialCommittee B7 validation
    # Accounts interest bearing Yes/No
    # Accounts Account type
    # Accounts Signature Requirement



class OldWorkbookToNew:
    if __name__ == '__main__':
        main()
