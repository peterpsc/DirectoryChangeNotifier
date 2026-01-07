from time import sleep

from selenium import webdriver
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import Persistence
import PrintHelper

class GDriveToSharePoint:

    def __init__(self, file_name):
        gdir_sp_urls = Persistence.get_lines(file_name)
        l = len(gdir_sp_urls)
        assert l == 2, f"Need 2 URLs, not {l}"
        self.g_expected_title, self.g_url = self.get_expected_title_url(gdir_sp_urls[0])
        self.s_expected_title, self.s_gdir_url = self.get_expected_title_url(gdir_sp_urls[1])

    def setup_browser(self, expected_title,  url):
        while True:
            try:
                self.driver = webdriver.Firefox()
                self.driver.set_page_load_timeout(800)
                self.driver.get(url)
                assert self.driver.title.__contains__(expected_title)
                break
            except Exception as e:
                raise e


    def create_folders(self):
        folders = self.gather_folders()
        self.create_sp_folders(folders)

    def gather_folders(self):
        PrintHelper.printInBox(f"gather_folders")
        self.setup_browser(self.g_expected_title, self.g_url)
        folders = []
        # TODO
        return folders


    def create_sp_folders(self, folders):
        pass

    def get_expected_title_url(self, line):
        parsed = line.split(",")
        assert len(parsed) == 2, "need title, url"
        return parsed[0], parsed[1]



if __name__ == '__main__':
    PrintHelper.printInBoxWithTime("DriveToSharePoint")

    g_s_us = GDriveToSharePoint("GDirToSharePointUSURLs.lst")
    g_s_us.create_folders()

    g_s_canada = GDriveToSharePoint("GDirToSharePointCanadaURLs.lst")
    g_s_canada.create_folders()

PrintHelper.printInBox()
