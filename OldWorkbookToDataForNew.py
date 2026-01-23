'''
OldWorkbookToNew.py uses openpyxl which has a problem saving files
UserWarning: Conditional Formatting extension is not supported and will be removed
UserWarning: Data Validation extension is not supported and will be removed

the new strategy is to use it to gather the data, but not to save the new file
we will need to write a macro to load the data and save the file, then delete the data file
This reading of the data file and saving may have to be executed for each file manually
'''
import openpyxl
import Persistence


class OldWorkbookToDataForNew:
    GROUP_TYPES = ["Barony","Canton","City","College","Event","Kingdom","Port","Principality","Project/Newsletter","Province","Shire","Sub Account"]
    KINGDOM = "East Kingdom"

    def __init__(self, old_workbook_file_path, new_data_file_path):
        self.old_workbook_file_path = old_workbook_file_path
        self.new_data_file_path = new_data_file_path
        self.old_workbook = openpyxl.load_workbook(self.old_workbook_file_path, data_only=True)
        self.new_data = []


    def save_summary(self):
        ws_old_contents = self.old_workbook["Contents"]
        name_of_branch = ws_old_contents["C8"].value
        print(f"Branch name = {name_of_branch}")
        group_type = None
        for g_type in self.GROUP_TYPES:
            if g_type.lower() in name_of_branch.lower():
                group_type = g_type
                break
        assert group_type, f"group_type = {group_type} not found"
        self.new_data.append(["Summary", "D6", group_type])
        self.new_data.append(["Summary", "D7", self.KINGDOM])
        state = ws_old_contents["C15"].value
        self.new_data.append(["Summary", "D8", state])  # TODO state from google drive if missing
        self.new_data.append(["Summary", "D9", name_of_branch])
        currency = ws_old_contents["C14"].value
        self.new_data.append(["Summary", "H8", currency])

    def save_exchequer(self):
        ws_old_contents = self.old_workbook["Contents"]
        exchequer_name = ws_old_contents["C10"].value
        self.new_data.append(["Exchequers", "C8", exchequer_name])
        ws_old_contact_info = self.old_workbook["CONTACT_INFO_1"]
        sca_name = ws_old_contact_info["D16"].value
        self.new_data.append(["Exchequers", "C9", sca_name])
        membership_no = ws_old_contact_info["H15"].value
        self.new_data.append(["Exchequers", "L8", membership_no])
        expiration_date = self.dmy(ws_old_contact_info["H16"].value)
        self.new_data.append(["Exchequers", "L9", expiration_date])
        home_address = ws_old_contact_info["D12"].value
        self.new_data.append(["Exchequers", "D10", home_address])
        city_town = ws_old_contact_info["D13"].value
        self.new_data.append(["Exchequers", "K10", city_town])
        state_or_province = ws_old_contact_info["F13"].value
        self.new_data.append(["Exchequers", "C11", state_or_province])
        zip_code = ws_old_contact_info["H13"].value
        self.new_data.append(["Exchequers", "G11", zip_code])
        home_phone = ws_old_contact_info["D14"].value
        alt_phone = ws_old_contact_info["F14"].value
        phone = self.get_phone(alt_phone, home_phone)
        self.new_data.append(["Exchequers", "C12", phone])
        personal_email = ws_old_contact_info["D15"].value
        self.new_data.append(["Exchequers", "H12", personal_email])

    def get_phone(self, home_phone, alt_phone):
        if alt_phone and home_phone:
            return home_phone + ", " + alt_phone
        else:
            return home_phone

    def save_deputy_exchequer_1(self):
        ws_old_contact_info = self.old_workbook["CONTACT_INFO_1"]
        deputy_exchequer_name = ws_old_contact_info["D22"].value
        self.new_data.append(["Exchequers", "C16", deputy_exchequer_name])
        deputy_sca_name = ws_old_contact_info["D27"].value
        self.new_data.append(["Exchequers", "C17", deputy_sca_name])
        membership_no = ws_old_contact_info["H26"].value
        self.new_data.append(["Exchequers", "L16", membership_no])
        expiration_date = self.dmy(ws_old_contact_info["H27"].value)
        self.new_data.append(["Exchequers", "L17", expiration_date])
        home_address = ws_old_contact_info["D23"].value
        self.new_data.append(["Exchequers", "D18", home_address])
        city_town = ws_old_contact_info["D24"].value
        self.new_data.append(["Exchequers", "K18", city_town])
        state_or_province = ws_old_contact_info["F24"].value
        self.new_data.append(["Exchequers", "C19", state_or_province])
        zip_code = ws_old_contact_info["H24"].value
        self.new_data.append(["Exchequers", "G19", zip_code])
        home_phone = ws_old_contact_info["D25"].value
        alt_phone = ws_old_contact_info["F25"].value
        phone = self.get_phone(home_phone, alt_phone)
        self.new_data.append(["Exchequers", "C20", phone])
        personal_email = ws_old_contact_info["D26"].value
        self.new_data.append(["Exchequers", "H20", personal_email])

    def save_deputy_exchequer_2(self):
        ws_old_contact_info = self.old_workbook["CONTACT_INFO_1"]
        deputy_exchequer_name = ws_old_contact_info["D30"].value
        self.new_data.append(["Exchequers", "C24", deputy_exchequer_name])
        sca_name = ws_old_contact_info["D35"].value
        self.new_data.append(["Exchequers", "C25", sca_name])
        membership_no = ws_old_contact_info["H34"].value
        self.new_data.append(["Exchequers", "L24", membership_no])
        expiration_date = self.dmy(ws_old_contact_info["H35"].value)
        self.new_data.append(["Exchequers", "L25", expiration_date])
        home_address = ws_old_contact_info["D31"].value
        self.new_data.append(["Exchequers", "D26", home_address])
        city_town = ws_old_contact_info["D32"].value
        self.new_data.append(["Exchequers", "K26", city_town])
        state_or_province = ws_old_contact_info["F32"].value
        self.new_data.append(["Exchequers", "C27", state_or_province])
        zip_code = ws_old_contact_info["H32"].value
        self.new_data.append(["Exchequers", "G27", zip_code])
        home_phone = ws_old_contact_info["D33"].value
        alt_phone = ws_old_contact_info["F33"].value
        phone = self.get_phone(home_phone, alt_phone)
        self.new_data.append(["Exchequers", "C28", phone])
        personal_email = ws_old_contact_info["D34"].value
        self.new_data.append(["Exchequers", "H28", personal_email])




    def save_financial_committee(self):
        ws_old_contents = self.old_workbook["Contents"]
        seneshal_name = ws_old_contents["C9"].value
        self.new_data.append(["FinancialCommittee", "C11", seneshal_name])
        ws_old_financial_committee = self.old_workbook["FINANCE_COMM_13"]
        seneshal_sca_name = ws_old_financial_committee["D18"].value
        self.new_data.append(["FinancialCommittee", "C12", seneshal_sca_name])
        seneshal_member_number = ws_old_financial_committee["E17"].value
        self.new_data.append(["FinancialCommittee", "D11", seneshal_member_number])
        seneshal_expiry_date = self.dmy(ws_old_financial_committee["F17"].value)
        self.new_data.append(["FinancialCommittee", "E11", seneshal_expiry_date])
        # TODO Do the Rest
        # TODO add Choices 2 or 3

    def save_primary_account(self):
        ws_old_primary_account = self.old_workbook["PRIMARY_ACCOUNT_2a"]
        bank_name = ws_old_primary_account["E13"].value
        self.new_data.append(["Accounts", "B9", bank_name])
        bank_account_title = ws_old_primary_account["E14"].value
        self.new_data.append(["Accounts", "B8", bank_account_title])
        bank_contact = ws_old_primary_account["F17"].value
        self.new_data.append(["Accounts", "B10", bank_contact])
        bank_account_type = ws_old_primary_account["E15"].value
        self.set_bank_account_type("B12", bank_account_type)
        signature_requirement = ws_old_primary_account["H15"].value
        self.set_signature_requirement("B13", signature_requirement)
        bank_account_number = ws_old_primary_account["E16"].value
        self.new_data.append(["Accounts", "B11", bank_account_number])
        balance = ws_old_primary_account["H19"].value
        self.new_data.append(["Accounts", "C16", balance])
        ledger_balance = ws_old_primary_account["H37"].value
        self.new_data.append(["Accounts", "C17", ledger_balance])
        interest_bearing = ws_old_primary_account["F38"].value
        self.set_interest_bearing("B14", interest_bearing)

        # TODO add bank name, type
        # signatories
        for i in range(0,5):
            self.save_primary_signatories(ws_old_primary_account, 42+i*2, 16+i)

    def save_primary_signatories(self, ws_old_primary_account, old_row, new_row):
        signatory_name = ws_old_primary_account[f"E{old_row}"].value
        self.new_data.append(["Accounts", f"E{new_row}", signatory_name])
        signatory_member_number = ws_old_primary_account[f"H{old_row}"].value
        self.new_data.append(["Accounts", f"I{new_row}", signatory_member_number])
        signatory_expiry_date = self.dmy(ws_old_primary_account[f"H{old_row+1}"].value)
        self.new_data.append(["Accounts", f"J{new_row}", signatory_expiry_date])
        #TODO add up to 6

    def save_secondary_signatories(self, ws_old_secondary_account, old_row, new_row):
        signatory_name = ws_old_secondary_account[f"D{old_row}"].value
        self.new_data.append(["Accounts", f"E{new_row}", signatory_name])
        signatory_member_number = ws_old_secondary_account[f"D{old_row + 1}"].value
        self.new_data.append(["Accounts", f"I{new_row}", signatory_member_number])
        signatory_expiry_date = self.dmy(ws_old_secondary_account[f"D{old_row + 2}"].value)
        self.new_data.append(["Accounts", f"J{new_row}", signatory_expiry_date])
        # TODO add up to 6
        # TODO add interest bearing

    def save_secondary_accounts(self):
        ws_old_contents = self.old_workbook["Contents"]
        ws_old_secondary_account = self.old_workbook["SECONDARY_ACCOUNTS_2b"]
        bank_name = ws_old_secondary_account["D13"].value
        self.new_data.append(["Accounts", "B24", bank_name])
        bank_account_title = ws_old_contents["C8"].value
        self.new_data.append(["Accounts", "B23", bank_account_title])
        # bank_contact = ws_old_secondary_account["F17"].value
        # ws_new_accounts["B10"] = bank_contact
        bank_account_type = ws_old_secondary_account["D16"].value
        self.set_bank_account_type( "B27", bank_account_type)
        signature_requirement = ws_old_secondary_account["D15"].value
        self.set_signature_requirement("B28", signature_requirement)
        self.new_data.append(["Summary","B20", bank_account_type])
        bank_account_number = ws_old_secondary_account["D14"].value
        self.new_data.append(["Accounts", "B26", bank_account_number])
        balance = ws_old_secondary_account["D19"].value
        self.new_data.append(["Accounts", "C31", balance])
        ledger_balance = ws_old_secondary_account["D25"].value
        self.new_data.append(["Accounts", "C32", ledger_balance])
        interest_bearing = ws_old_secondary_account["D17"].value
        self.set_interest_bearing("B29", interest_bearing)

        # signatories
        for i in range(0, 5):
            self.save_secondary_signatories(ws_old_secondary_account, 27 + i * 3, 31 + i)

        # TODO add up to 4 secondary accounts


    def set_signature_requirement(self, cell, signature_requirement):
        choices = ["Single","Dual"]
        choice = self.get_choice(choices, signature_requirement)
        self.new_data.append(["Accounts", cell, choice])

    def set_interest_bearing(self, cell, interest_bearing):
        choices = ["Yes","No"]
        choice = self.get_choice(choices, interest_bearing)
        self.new_data.append(["Accounts", cell, choice])

    def set_bank_account_type(self, cell, bank_account_type):
        choices = ["Checking","Savings","CD/GIC","Money Market"]
        choice = self.get_choice(choices, bank_account_type)
        self.new_data.append(["Accounts", cell, choice])

    def save_funds(self):
        ws_old_funds = self.old_workbook["FUNDS_14"]
        # TODO from

    def save_outstanding(self):
        #TODO PRIMARY_ACCOUNT_2a 1. Balance from bank statement at end of period (6 of them)
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
        for choice in choices:
            if choice.lower() == value.lower():
                return choice
            if value.lower() == choice.lower()[0:len(value)]: # permit "Saving" to match "Savings"
                return choice
            if choice.lower() == value.lower()[0:len(choice)]: # permit "Dual Signature" to match "Dual"
                return choice
        print(f"Invalid choice: {value}")
        return value

    def save_data(self):
        lines = []
        for data in self.new_data:
            lines.append(f'"{data[0]}","{data[1]}","{data[2]}"')

        Persistence.write_lines(self.new_data_file_path, lines, path_type=Persistence.FILE_PATH)

    def dmy(self, dt):
        if not dt:
            return None
        if type(dt) == str:
            return dt.replace(" ", "")
        dmy = dt.strftime("%m/%d/%Y")
        return dmy



def main():
    wbs = OldWorkbookToDataForNew("Resources\\EK-Towers 2025-Q4.xlsm", "Resources\\SCA Exchequer Report - 2026-02.csv")
    wbs.save_summary()
    wbs.save_exchequer()
    wbs.save_deputy_exchequer_1()
    wbs.save_deputy_exchequer_2()
    wbs.save_financial_committee()
    wbs.save_primary_account()
    wbs.save_secondary_accounts()
    wbs.save_funds()
    wbs.save_liabilities()
    wbs.save_outstanding()
    wbs.save_assets()
    wbs.save_data()

    # TODO fix data validation https://openpyxl.readthedocs.io/en/3.1/validation.html
    # FinancialCommittee B7 validation
    # Accounts interest bearing Yes/No
    # Accounts Account type
    # Accounts Signature Requirement



class OldWorkbookToNew:
    if __name__ == '__main__':
        main()
