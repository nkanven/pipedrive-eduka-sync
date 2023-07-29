import datetime
import json
import time

import requests as requests

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
        if pipeline_ids.__len__() > 1:
            admitted_deals = self.get_deals_from_stage_by_pipelines(pipeline_ids, "admitted")
        else:
            admitted_deals = self.get_deals_from_stage_by_pipeline(pipeline_ids[0], "admitted")

        # admitted_deals_datas = admitted_deals["datas"]
        print(f"{admitted_deals.__len__()} admitted deals found")
        if admitted_deals.__len__() == 0:
            error = "No admitted deals found"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for adm in admitted_deals[0]:
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

        # print(parent_with_emails)
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
        self.clean_deals = admitted_deals
        if self.clean_deals.__len__() == 0:
            error = "No student with first name found"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

    def parse_data(self):
        print("Total deals", self.clean_deals.__len__())
        # i = 1000 #TODO: Place to handle just a few number of deals. To be removed
        sync_data = ()
        for deals in self.clean_deals:
            for deal in deals:
                product = self.get_product_code(deal["id"])
                if product is not None:
                    product_id = product[0]["product_id"]
                    student_first_name = deal[self.get_pipedrive_param_name_for["student first name"]]
                    student_last_name = deal[self.get_pipedrive_param_name_for["student last name"]]
                    gender = deal[self.get_pipedrive_param_name_for["email"]]
                    school_branch_code = self.get_school_branch_code(product_id)
                    parent_first_name = deal[self.get_pipedrive_param_name_for["parent first name"]]
                    parent_last_name = deal[self.get_pipedrive_param_name_for["parent last name"]]
                    parent_email = deal[self.get_pipedrive_param_name_for["email"]]
                    parent_phone = deal[self.get_pipedrive_param_name_for["phone"]]
                    student_id = str(datetime.datetime.now().timestamp()).replace(".", "")
                    time.sleep(1)
                    parent_id = str(datetime.datetime.now().timestamp()).replace(".", "")
                    time.sleep(1)
                    family_id = self.get_family_id(self.get_school_parameter(self.school, "abbr"), self.base_url, self.school, parent_email)

                    print(family_id, student_id, school_branch_code, product_id, student_first_name, student_last_name, gender,
                          parent_first_name, parent_last_name, parent_email, parent_phone)

                    # TODO: For testing purpose; to Remove this condition
                    if parent_email is None:
                        continue

                    if family_id is not None:
                        sync_data += (
                            [family_id, student_id, student_first_name, student_last_name, gender, school_branch_code, parent_id, '', '', '', '', deal["id"]],
                        )
                    else:
                        sync_data += (
                            [str(datetime.datetime.now().timestamp()).replace(".", ""), student_id, student_first_name, student_last_name, gender, school_branch_code, parent_id, parent_first_name, parent_last_name, parent_email, parent_phone, deal["id"]],
                        )
                    i += 1

                    # if i == 1005:
                    #     break

        heads = ["Family ID", "Student ID", "First name (student)", "Last name (student)", "Gender (student)", "School branch code",
                 "Parent ID", "Firs name (parent)", "Last name (parent)", "Email address (parent)", "Mobile phone number (parent)", "Deal ID"]
        self.create_xlsx("pipedrive_to_eduka", heads, sync_data)

    def import_to_eduka(self):
        endpoint = self.base_url + "api.php?K=" + self.get_school_parameter(self.school, "api_key") \
                   + "&A=IMPORTDATA&PROFILE=" + str(self.get_school_parameter(self.school,
                                                                          "deals_import_profileID")) \
                   + "&FILEURL=http://" + self.get_ip_address() + "/assets/pipedrive_to_eduka.xlsx" \
                                                                  "&SEPARATOR=comma&ASYNC=0"

        try:
            response_text = "Import Failed"
            session = self.get_session()
            with session.get(endpoint) as r:
                if "OK-PROCESSED" in r.text:
                    response_text = "Import successful"
        except requests.exceptions.ConnectionError as e:
            self.errors.append(
                ("ConnectionError occurred on " + self.school, "Error summary " + str(e))
            )
            self.error_logger.critical("ConnectionError occurred", exc_info=True)
            raise EdukaPipedriveImportException(self.service_name, self.school, str(e))
        finally:
            return response_text

    def run(self, cmd: str):
        print(self.get_ip_address(), self.import_to_eduka())
        # name = {"Deals from Eduka": "eduka_stageID", "Admitted": "admitted_stageID", "Eduka Application":"eduka_stageID"}
        #
        # stages_dict = {}
        # for stage in self.ask_pipedrive("stages"):
        #     if stage['name'] in ["Deals from Eduka", "Admitted", "Eduka Application"]:
        #         if stage['pipeline_id'] in stages_dict.keys():
        #             stages_dict[stage['pipeline_id']].append(f'"{name[stage["name"]]}" : "{stage["id"]}')
        #         else:
        #             stages_dict[stage['pipeline_id']] = [f'"{name[stage["name"]]}" : "{stage["id"]}']
        # # print(stage['id'], stage['name'], stage['pipeline_id'])
        # print(stages_dict)
        # with open("stages.json", "w") as f:
        #     f.write(json.dumps(stages_dict))
        # exit()
        try:
            pipelines = []
            stages = []
            for pl in self.ask_pipedrive("users"):
                pipelines.append(pl)
                # print(f"{pl['id']}, {pl['name']}, {pl['url_title']}, {pl['active']}")
                print(pl['id'], pl['email'], sep=",")

            # print(pipelines)

            # print(self.get_deals_from_stage_by_pipeline(161, "admitted"))
            # exit()
            self.check_conditions()
            # print("Clean deals ", self.clean_deals.__len__(), self.clean_deals)
            self.parse_data()
            print(self.import_to_eduka())
        except EdukaPipedriveNoDealsFoundException as e:
            print(str(e))
            self.error_logger.critical("Eduka Pipedrive Not Deals Found Exception occured", exc_info=True)
        except EdukaPipedriveImportException as e:
            print(str(e))
            self.error_logger.critical("Eduka Pipedrive Pipedrive import Exception occured", exc_info=True)

