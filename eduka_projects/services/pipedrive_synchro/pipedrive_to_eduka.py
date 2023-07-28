import datetime
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
        # pipeline_ids = [124, 125, 126, 164, 158, 160, 159, 120, 122, 123, 161, 142, 143, 145, 147, 157, 151, 144, 135,
        #                 101, 110]
        # pipeline_ids_bis = [50, 65, 76, 163, 176, 177, 166, 172, 173, 165, 167, 174, 168, 175, 169]
        pipeline_ids = self.get_school_parameter(self.school)["pipeline_ids"].split(",")
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
            # admitted_deals = admitted_deals + self.get_deals_from_stage_by_pipelines(pipeline_ids_bis, "admitted")
        else:
            admitted_deals = self.get_deals_from_stage_by_pipeline(pipeline_ids[0], "admitted")

        # admitted_deals_datas = admitted_deals["datas"]
        print(f"{admitted_deals.__len__()} admitted deals found")
        if admitted_deals.__len__() == 0:
            error = "No admitted deals found"
            # raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for adm in admitted_deals[0]:
            if adm['status'].lower() not in ["won", "lost"]:
                not_won_losses.append(adm)

        print(f"{not_won_losses.__len__()} not won losses deals found")
        if not_won_losses.__len__() == 0:
            error = "All deals were either WON or LOST"
            # raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for not_won_loss in not_won_losses:
            # Blank student Id field
            if not_won_loss["0dfe2a7c991908de1eb76779d5a99487c3955f9b"] is None:
                blank_student_ids.append(not_won_loss)

        print(f"{blank_student_ids.__len__()} blank students id deals")
        if blank_student_ids.__len__() == 0:
            error = "No deals with blank student IDs found"
            # raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for blank_student_id in blank_student_ids:
            if blank_student_id['f138752f358c149c11bce02f6003a718d36d3575'] is not None \
                    and blank_student_id['f138752f358c149c11bce02f6003a718d36d3575'] in self.pipedrive_gender.keys():
                students_with_gender.append(blank_student_id)

        print(f"{students_with_gender.__len__()} students with gender")
        if students_with_gender.__len__() == 0:
            error = "No student with gender (G/F) found."
            # raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for student_with_gender in students_with_gender:
            if student_with_gender['f6bbcc60845993baedec912a5d4b2056d92fe5a8'] is not None \
                    and student_with_gender['f6bbcc60845993baedec912a5d4b2056d92fe5a8'].find("@") != -1:
                parent_with_emails.append(student_with_gender)

        # print(parent_with_emails)
        print(f"{parent_with_emails.__len__()} parents with email deals")
        if parent_with_emails.__len__() == 0:
            error = "No parent was found with an email address"
            # raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        # One and only one product should be attached to the deal
        for parent_with_email in parent_with_emails:
            if parent_with_email['products_count'] == 1:
                deals_with_products.append(parent_with_email)

        print(f"{deals_with_products.__len__()} deals with only 1 product")
        if deals_with_products.__len__() == 0:
            error = "No deal with only 1 product was found."
            # raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        # Get Student first name
        for deals_with_product in deals_with_products:
            if deals_with_product["88a0962f7916a41085bf8545f3b9433485140da5"] is not None:
                self.clean_deals.append(deals_with_product)

        print(f"{self.clean_deals.__len__()} clean deals left")
        self.clean_deals = admitted_deals
        if self.clean_deals.__len__() == 0:
            error = "No student with first name found"
            # raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

    def parse_data(self):
        print("Total deals", self.clean_deals.__len__())
        i = 1000 #TODO: Place to handle just a few number of deals. To be removed
        sync_data = ()
        for deals in self.clean_deals:
            for deal in deals:
                product = self.get_product_code(deal["id"])
                if product is not None:
                    product_id = product[0]["product_id"]
                    student_first_name = deal["88a0962f7916a41085bf8545f3b9433485140da5"]
                    student_last_name = deal["525ad777ef8851736fd9a46986d5c5c26541fdc5"]
                    gender = deal["f138752f358c149c11bce02f6003a718d36d3575"]
                    school_branch_code = self.get_school_branch_code(product_id)
                    parent_first_name = deal["dc4ec04f55ae86eab296ce0ada292a9237c77a35"]
                    parent_last_name = deal["bb03d0847076fe0486020b79c21dc58b06b43251"]
                    parent_email = deal["f6bbcc60845993baedec912a5d4b2056d92fe5a8"]
                    parent_phone = deal["116182a46dd67c25cdd4ced5ec4f7d0ed1526f15"]
                    student_id = str(datetime.datetime.now().timestamp()).split(".")[0]
                    time.sleep(1)
                    parent_id = str(datetime.datetime.now().timestamp()).split(".")[0]
                    time.sleep(1)
                    family_id = self.get_family_id(self.get_school_parameter(self.school, "abbr"), self.base_url, self.school, parent_email)

                    print(family_id, student_id, school_branch_code, product_id, student_first_name, student_last_name, gender,
                          parent_first_name, parent_last_name, parent_email, parent_phone)

                    # TODO: For testing purpose; to Remove this condition
                    if parent_email is None:
                        continue

                    if family_id is not None:
                        sync_data += (
                            [family_id, student_id, student_first_name, student_last_name, gender, school_branch_code, parent_id,'','','','',deal["id"]],
                        )
                    else:
                        sync_data += (
                            [str(datetime.datetime.now().timestamp()).split(".")[0], student_id, student_first_name, student_last_name, gender, school_branch_code, parent_id, parent_first_name, parent_last_name, parent_email, parent_phone, deal["id"]],
                        )
                    i += 1

                    if i == 1005:
                        break

        heads = ["Family ID", "Student ID", "First name (student)", "Last name (student)", "Gender (student)", "School branch code",
                 "Parent ID", "Firs name (parent)", "Last name (parent)", "Email address (parent)", "Mobile phone number (parent)", "Deal ID"]
        self.create_xlsx("pipedrive_to_eduka", heads, sync_data)

    def import_to_eduka(self):
        endpoint = self.base_url + "api.php?K=" + self.get_school_parameter(self.school, "api_key") \
                   + "&A=IMPORTDATA&PROFILE=" + self.get_school_parameter(self.school,
                                                                          "import_profile_id_for_pipedrive_sync") \
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
        # print(self.get_ip_address(), self.import_to_eduka())
        # exit()
        try:
            pipelines = []
            stages = []
            for pl in self.ask_pipedrive("pipeline"):
                pipelines.append(pl)
                # print(f"{pl['id']}, {pl['name']}, {pl['url_title']}, {pl['active']}")

            # print(pipelines)

            # print(self.get_deals_from_stage_by_pipeline(161, "admitted"))
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

