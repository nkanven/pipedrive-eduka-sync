"""
# PipeDrive Synchro Service

This service objective is to synchronize deals from PipeDrive to Eduka Platform, and from Eduka Platform to PipeDrive
"""
import time
import csv

import requests
from eduka_projects.services import ServiceManager
from eduka_projects.bootstrap import platform
from eduka_projects.utils.eduka_exceptions import EdukaPipedriveNoPipelineFoundException

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import xlsxwriter

import json


class PipedriveService(ServiceManager):
    def __init__(self):
        super().__init__()
        self.pipedrive_params = self.parameters["global"]["pipedrive"]
        self.gender = {
            "103": "f",
            "102": "g"
        }

    def ask_pipedrive(self, endpoint, **kwargs):
        url = self.pipedrive_params["base_url"] + self.pipedrive_params["endpoints"][endpoint] + "?api_token=" + \
              self.pipedrive_params["api_token"]

        path = ""

        for key, value in kwargs.items():
            if key == "path":
                path += f"/{value}"
                continue

            url += "&" + key + "=" + str(value)

        url = url.replace("?", f"{path}?")
        # print(url)

        payload = {}
        headers = {
            'Accept': 'application/json'
        }

        session = self.get_session()
        # response = session.get(url, headers=headers, data=payload)
        response = requests.get(url, headers=headers, data=payload)

        return json.loads(response.text)["data"]

    def get_admitted_stage_id(self, pipeline_id, stage_name="admitted"):
        stage_id = None
        stages = self.ask_pipedrive("stages", pipeline_id=pipeline_id)
        for stage in stages:
            if stage['name'].lower() == stage_name:
                stage_id = stage['id']

        return stage_id

    def get_deals_from_stage_by_pipeline(self, pipeline_id: int, stage_name: str):
        deals = []
        stage_id = self.get_admitted_stage_id(pipeline_id, stage_name)
        if stage_id is not None:
            deals = self.ask_pipedrive("deals", stage_id=stage_id)

        return deals

    def get_product_code(self, deal_id):
        path = str(deal_id) + "/products/"
        product = self.ask_pipedrive("deals", path=path)
        return product

    def get_school_branch_code(self, product_id):
        path = f"products/{product_id}"
        school_bcode = None
        product = self.ask_pipedrive("products", path=product_id)

        if product is not None:
            school_bcode = product["639757ba26481440820c9b29d205bba9ba25dcb2"]
        return school_bcode

    def get_deals_from_stage_by_pipelines(self, pipeline_ids: list, stage_name: str):
        deals = []
        try:
            print(pipeline_ids, stage_name)
            for pipeline_id in pipeline_ids:
                stage_id = self.get_admitted_stage_id(pipeline_id, stage_name)
                print("stage id", stage_id)
                if stage_id is not None:
                    deals.append(self.ask_pipedrive("deals", stage_id=stage_id))
        except Exception:
            self.error_logger.critical("Exception occured", exc_info=True)
        finally:
            return deals

    def create_eduka_file(self, file_name, heads, content):
        with open(f'{file_name}.csv', "w") as f:
            write = csv.writer(f, delimiter=",")
            write.writerow(heads)
            write.writerows(content)


    def create_xlsx(self, file_name, heads, contents):
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(f'{file_name}.xlsx')
        worksheet = workbook.add_worksheet()
        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({'bold': 1})
        # Adjust the column width.
        worksheet.set_column(1, 1, 35)
        i = 0
        row = 1
        col = 0
        for head in heads:
            letter = 65 + i
            worksheet.write(f"{chr(letter)}1", head, bold)
            i += 1

        for family_id, student_id, student_first_name, student_last_name, gender, school_bcode, parent_id, parent_first_name, parent_last_name, email, phone, deal_id in contents:
            worksheet.write_string(row, col, str(family_id))
            worksheet.write_string(row, col + 1, student_id)
            worksheet.write_string(row, col + 2, student_first_name)
            worksheet.write_string(row, col + 3, student_last_name)
            worksheet.write_string(row, col + 4, self.gender[str(gender)])
            worksheet.write_string(row, col + 5, school_bcode)
            worksheet.write_string(row, col + 6, parent_id)
            worksheet.write_string(row, col + 7, parent_first_name)
            worksheet.write_string(row, col + 8, parent_last_name)
            worksheet.write_string(row, col + 9, email)
            worksheet.write_string(row, col + 10, phone)
            worksheet.write_string(row, col + 11, str(deal_id))
            row += 1

        workbook.close()

    def get_family_id(self, abbr, base_url, school, parent_email):
        fam_id = None
        family_ids = self.get_guardians(abbr, base_url, school)
        for family_id in family_ids:
            if family_id[2] == parent_email:
                fam_id = family_id[0]
        print("Family ", fam_id)
        return fam_id
