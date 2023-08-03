import datetime
import json
import os
import time

import requests as requests
from eduka_projects.utils.rialization import serialize
from eduka_projects.services.pipedrive_synchro import PipedriveService
from eduka_projects.utils.eduka_exceptions import EdukaPipedriveNoDealsFoundException, \
    EdukaPipedriveNoPipelineFoundException, EdukaPipedriveImportException


class PipedriveToEduka(PipedriveService):
    def __init__(self, school):
        super().__init__()
        self.school = school
        self.service_name = "Pipedrive to Eduka"
        self.clean_deals = []
        self.base_url = self.get_school_parameter(self.school, "base_url")
        self.student_id = None
        self.deal_id = None
        self.notifications = {"imported_deals": [], "school": self.school, "error": ""}

        # TODO: Use training pipeline

    def check_conditions(self):
        pipeline_ids = self.get_school_parameter(self.school)["pipedrive_pipelines"].keys()
        if pipeline_ids.__len__() == 0:
            error = "No pipeline found."
            raise EdukaPipedriveNoPipelineFoundException(self.service_name, self.school, error)

        not_won_losses = []
        blank_student_ids = []
        parent_with_emails = []
        deals_with_products = []
        students_with_gender = []

        print(f"Total pipeline found {pipeline_ids.__len__()}")
        if pipeline_ids.__len__() == 0:
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, "No pipeline found")

        if pipeline_ids.__len__() > 1:
            admitted_deals = self.get_deals_from_stage_by_pipelines(pipeline_ids, "admitted")
        else:
            admitted_deals = self.get_deals_from_stage_by_pipeline(list(pipeline_ids)[0], "admitted")

        print(f"{admitted_deals.__len__()} admitted deals found")

        if admitted_deals.__len__() == 0:
            error = "No admitted deals found"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for admitted_deal in admitted_deals:
            for adm in admitted_deal:
                if adm['status'].lower() not in ["won", "lost"]:
                    not_won_losses.append(adm)

        print(f"{not_won_losses.__len__()} not won losses deals found")
        if not_won_losses.__len__() == 0:
            error = "All deals were either WON or LOST"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for not_won_loss in not_won_losses:
            # Blank student Id field
            if not_won_loss[self.get_pipedrive_param_name_for["student id"]] is None:
                blank_student_ids.append(not_won_loss)

        print(f"{blank_student_ids.__len__()} blank students id deals")
        if blank_student_ids.__len__() == 0:
            error = "No deals with blank student IDs found"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for blank_student_id in blank_student_ids:
            if blank_student_id[self.get_pipedrive_param_name_for["gender"]] is not None \
                    and blank_student_id[self.get_pipedrive_param_name_for["gender"]] in self.pipedrive_gender.keys():
                students_with_gender.append(blank_student_id)

        print(f"{students_with_gender.__len__()} students with gender")
        if students_with_gender.__len__() == 0:
            error = "No student with gender (G/F) found."
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for student_with_gender in students_with_gender:
            if student_with_gender[self.get_pipedrive_param_name_for["email"]] is not None \
                    and student_with_gender[self.get_pipedrive_param_name_for["email"]].find("@") != -1:
                parent_with_emails.append(student_with_gender)

        print(f"{parent_with_emails.__len__()} parents with email deals")
        if parent_with_emails.__len__() == 0:
            error = "No parent was found with an email address"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        # One and only one product should be attached to the deal
        for parent_with_email in parent_with_emails:
            if parent_with_email['products_count'] == 1:
                deals_with_products.append(parent_with_email)

        print(f"{deals_with_products.__len__()} deals with only 1 product")
        if deals_with_products.__len__() == 0:
            error = "No deal with only 1 product was found."
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        # Get Student first name
        for deals_with_product in deals_with_products:
            if deals_with_product[self.get_pipedrive_param_name_for["student first name"]] is not None:
                self.clean_deals.append(deals_with_product)

        print(f"{self.clean_deals.__len__()} clean deals left")
        if self.clean_deals.__len__() == 0:
            error = "No student with first name found"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

    def parse_data(self):
        print("Total deals", self.clean_deals.__len__())
        print(self.clean_deals)
        # i = 1000 #TODO: Place to handle just a few number of deals. To be removed
        sync_data = ()
        imported_deals = []

        for deal in self.clean_deals:
            product = self.get_product_code(deal["id"])
            if product is not None:
                self.deal_id = str(deal["id"]).strip("'")
                product_id = product[0]["product_id"]
                student_first_name = deal[self.get_pipedrive_param_name_for["student first name"]]
                student_last_name = deal[self.get_pipedrive_param_name_for["student last name"]]
                gender = self.genders_to_eduka[int(deal[self.get_pipedrive_param_name_for["gender"]])]
                school_branch_code = self.get_school_branch_code(product_id)
                parent_first_name = deal[self.get_pipedrive_param_name_for["parent first name"]]
                parent_last_name = deal[self.get_pipedrive_param_name_for["parent last name"]]
                parent_email = deal[self.get_pipedrive_param_name_for["email"]]
                parent_phone = deal[self.get_pipedrive_param_name_for["phone"]]
                self.student_id = str(datetime.datetime.now().timestamp()).replace(".", "")
                time.sleep(1)
                parent_id = str(datetime.datetime.now().timestamp()).replace(".", "")
                time.sleep(1)
                family_id = self.get_family_id(self.get_school_parameter(self.school, "abbr"), self.base_url,
                                               self.school, parent_email)

                if family_id is not None:
                    sync_data = (
                        [family_id, self.student_id, student_first_name, student_last_name, gender, school_branch_code,
                         '', '', '', '', '', self.deal_id],
                    )
                else:
                    sync_data = (
                        [str(datetime.datetime.now().timestamp()).replace(".", ""), self.student_id, student_first_name,
                         student_last_name, gender, school_branch_code, parent_id, parent_first_name,
                         parent_last_name, parent_email, parent_phone, self.deal_id],
                    )

                heads = ["Family ID", "Student ID", "First name (student)", "Last name (student)", "Gender (student)",
                         "School branch code",
                         "Parent ID", "Firs name (parent)", "Last name (parent)", "Email address (parent)",
                         "Mobile phone number (parent)", "Deal ID"]
                self.create_xlsx("pipedrive_to_eduka", heads, sync_data)
                import_status = self.import_to_eduka()
                print(f"Import to eduka status for {self.school}: {import_status}")
                if import_status:
                    print("Sync data", sync_data.__len__(), sync_data)
                    imported_deals.append([self.student_id, self.deal_id])
                else:
                    self.notifications["error"] = "Data import to Eduka error occured"

        self.notifications["imported_deals"] = imported_deals

    def import_to_eduka(self) -> bool:
        print("Import to Eduka")
        endpoint = self.base_url + "api.php?K=" + self.get_school_parameter(self.school, "api_key") \
                   + "&A=IMPORTDATA&PROFILE=" + str(self.get_school_parameter(self.school,
                                                                              "deals_import_profileID")) \
                   + "&FILEURL=http://" + self.get_ip_address() + "/assets/pipedrive_to_eduka.xlsx" \
                                                                  "&SEPARATOR=comma&ASYNC=0"
        print("Endpoint ", endpoint)
        try:
            response = False
            session = self.get_session()
            with session.get(endpoint) as r:
                if "OK-PROCESSED" in r.text:
                    response = True
                    update_deal_param = {
                        self.get_pipedrive_param_name_for["student id"]: self.student_id
                    }
                    self.update_deal(self.deal_id, update_deal_param)
        except requests.exceptions.ConnectionError as e:
            self.notifications["error"] = str(e)
            self.error_logger.critical("ConnectionError occurred", exc_info=True)
            raise EdukaPipedriveImportException(self.service_name, self.school, str(e))
        finally:
            try:
                os.remove("pipedrive_to_eduka.xlsx")
            except FileNotFoundError:
                pass

            return response

    def run(self, cmd: str):
        try:
            self.check_conditions()
            self.parse_data()
        except EdukaPipedriveNoDealsFoundException as e:
            print(str(e))
            self.notifications["error"] = str(e)
            self.error_logger.critical("Eduka Pipedrive Not Deals Found Exception occured", exc_info=True)
        except EdukaPipedriveImportException as e:
            print(str(e))
            self.notifications["error"] = str(e)
            self.error_logger.critical("Eduka Pipedrive Pipedrive import Exception occured", exc_info=True)
        except Exception as e:
            print(str(e))
            self.notifications["error"] = str(e)
            self.error_logger.critical("Eduka to Pipeline exception occurred", exc_info=True)
        finally:
            f_name = "mail" + cmd + "-" + self.get_school_parameter(self.school, "abbr")
            f_name_path = os.path.join(self.autobackup_memoize, f_name)
            print("self notif ", self.notifications)
            serialize(f_name_path, self.notifications)
            self.delete_product_memo()
