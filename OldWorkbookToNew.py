import openpyxl

class OldWorkbookToNew:
    GROUP_TYPES = ["Barony","Canton","City","College","Event","Kingdom","Port","Principality","Project/Newsletter","Province","Shire","Sub Account"]
    KINGDOM = "East Kingdom"

    def __init__(self, old_workbook_file_path, new_workbook_file_path):
        self.old_workbook_file_path = old_workbook_file_path
        self.new_workbook_file_path = new_workbook_file_path
        self.old_workbook = openpyxl.load_workbook(self.old_workbook_file_path)
        self.new_workbook = openpyxl.load_workbook(self.new_workbook_file_path)

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
        print(f"Group type = {group_type}")
        ws_new_summary = self.new_workbook["Summary"]
        ws_new_summary["D6"] = group_type
        ws_new_summary["D7"] = self.KINGDOM
        state = ws_old_contents["C15"].value
        ws_new_summary["D8"] = state  # state from google drive if missing
        ws_new_summary["D9"] = name_of_branch
        currency = ws_old_contents.cell(14, 3).value
        ws_new_summary["H8"] = currency

    def save_exchequer(self):
        ws_old_contents = self.old_workbook["Contents"]
        ws_new_exchequers = self.new_workbook["Exchequers"]
        exchequer_name = ws_old_contents["C10"].value
        ws_new_exchequers["C8"] = exchequer_name
        ws_old_contact_info = self.old_workbook["CONTACT_INFO_1"]
        sca_name = ws_old_contact_info["D16"].value
        ws_new_exchequers["C9"] = sca_name
        membership_no = ws_old_contact_info["H15"].value
        ws_new_exchequers["L8"] = membership_no
        expiration_date = ws_old_contact_info["H16"].value
        ws_new_exchequers["L9"] = expiration_date
        home_address = ws_old_contact_info["D12"].value
        ws_new_exchequers["D10"] = home_address
        city_town = ws_old_contact_info["D13"].value
        ws_new_exchequers["K10"] = city_town
        state_or_province = ws_old_contact_info["F13"].value
        ws_new_exchequers["C11"] = state_or_province
        zip_code = ws_old_contact_info["H13"].value
        ws_new_exchequers["G11"] = zip_code
        home_phone = ws_old_contact_info["D14"].value
        alt_phone = ws_old_contact_info["F14"].value
        ws_new_exchequers["C12"] = home_phone + ", " + alt_phone
        personal_email = ws_old_contact_info["D15"].value
        ws_new_exchequers["H12"] = personal_email

    def save_deputy_exchequer(self):
        ws_old_contents = self.old_workbook["Contents"]
        ws_new_exchequers = self.new_workbook["Exchequers"]
        exchequer_name = ws_old_contents["C10"].value
        ws_new_exchequers["C8"] = exchequer_name
        ws_old_contact_info = self.old_workbook["CONTACT_INFO_1"]
        sca_name = ws_old_contact_info["D16"].value
        ws_new_exchequers["C9"] = sca_name
        membership_no = ws_old_contact_info["H15"].value
        ws_new_exchequers["L8"] = membership_no
        expiration_date = ws_old_contact_info["H16"].value
        ws_new_exchequers["L9"] = expiration_date
        home_address = ws_old_contact_info["D12"].value
        ws_new_exchequers["D10"] = home_address
        city_town = ws_old_contact_info["D13"].value
        ws_new_exchequers["K10"] = city_town
        state_or_province = ws_old_contact_info["F13"].value
        ws_new_exchequers["C11"] = state_or_province
        zip_code = ws_old_contact_info["H13"].value
        ws_new_exchequers["G11"] = zip_code
        home_phone = ws_old_contact_info["D14"].value
        alt_phone = ws_old_contact_info["F14"].value
        ws_new_exchequers["C12"] = home_phone + ", " + alt_phone
        personal_email = ws_old_contact_info["D15"].value
        ws_new_exchequers["H12"] = personal_email




    def save_financial_committee(self):
        ws_old_contents = self.old_workbook["Contents"]
        ws_new_financial_committee = self.new_workbook["FinancialCommittee"]
        seneshal_name = ws_old_contents["C9"].value
        ws_new_financial_committee["C11"] = seneshal_name
        ws_old_financial_committee = self.old_workbook["FINANCE_COMM_13"]
        #TODO

    def save_primary_account(self):
        ws_old_contents = self.old_workbook["Contents"]
        ws_new_primary_account = self.new_workbook["PrimaryAccount"]
        #TODO

    def save_secondary_accounts(self):
        ws_old_contents = self.old_workbook["Contents"]
        ws_new_secondary_accounts = self.new_workbook["SecondaryAccounts"]
        #TODO

    def save_starting_balances(self):
        ws_old_contents = self.old_workbook["Contents"]
        ws_new_starting_balances = self.new_workbook["StartingBalances"]
        #TODO

def main():
    wbs = OldWorkbookToNew("Resources\\EK-Towers 2025-Q4.xlsm", "Resources\\SCA Exchequer Report - 2026-02.xlsx")
    wbs.save_summary()
    wbs.save_exchequer()
    wbs.save_deputy_exchequer()
    wbs.save_financial_committee()
    wbs.save_primary_account()
    wbs.save_secondary_accounts()
    wbs.save_starting_balances()

    wbs.new_workbook.save("Resources\\EK-Towers 2026-Q1 modified.xlsm")




class OldWorkbookToNew:
    if __name__ == '__main__':
        main()
