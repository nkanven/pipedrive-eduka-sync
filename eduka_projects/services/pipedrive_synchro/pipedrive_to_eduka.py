from eduka_projects.services.pipedrive_synchro import PipedriveService
from eduka_projects.utils.eduka_exceptions import EdukaPipedriveNoDealsFoundException, EdukaPipedriveNoPipelineFoundException


class PipedriveToEduka(PipedriveService):
    def __init__(self, school):
        super().__init__()
        self.school = school
        self.service_name = "Pipedrive to Eduka"
        self.clean_deals = []

    def check_conditions(self):
        pipeline_ids = self.get_school_parameter(self.school)["pipeline_ids"].split(",")
        if pipeline_ids.__len__() == 0:
            error = "No pipeline found."
            raise EdukaPipedriveNoPipelineFoundException(self.service_name, self.school, error)

        not_won_losses = []
        blank_student_ids = []
        parent_with_emails = []
        deals_with_products = []
        students_with_gender = []

        if pipeline_ids.__len__() > 1:
            admitted_deals = self.get_deals_from_stage_by_pipelines(pipeline_ids, "admitted")
        else:
            admitted_deals = self.get_deals_from_stage_by_pipeline(pipeline_ids[0], "admitted")

        # admitted_deals_datas = admitted_deals["datas"]
        if admitted_deals.__len__() == 0:
            error = "No admitted deals found"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for adm in admitted_deals[0]:
            if adm['status'].lower() not in ["won", "lost"]:
                not_won_losses.append(adm)

        if not_won_losses.__len__() == 0:
            error = "All deals were either WON or LOST"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for not_won_loss in not_won_losses:
            # Blank student Id field
            if not_won_loss["0dfe2a7c991908de1eb76779d5a99487c3955f9b"] is None:
                blank_student_ids.append(not_won_loss)

        if blank_student_ids.__len__() == 0:
            error = "No deals with blank student IDs found"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for blank_student_id in blank_student_ids:
            if blank_student_id['f138752f358c149c11bce02f6003a718d36d3575'] is not None \
                    and blank_student_id['f138752f358c149c11bce02f6003a718d36d3575'] in self.gender.keys():
                students_with_gender.append(blank_student_id)

        if students_with_gender.__len__() == 0:
            error = "No student with gender (G/F) found."
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        for student_with_gender in students_with_gender:
            if student_with_gender['f6bbcc60845993baedec912a5d4b2056d92fe5a8'] is not None \
                    and student_with_gender['f6bbcc60845993baedec912a5d4b2056d92fe5a8'].find("@") != -1:
                parent_with_emails.append(student_with_gender)

        if parent_with_emails.__len__() == 0:
            error = "No parent was found with an email address"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        # One and only one product should be attached to the deal
        for parent_with_email in parent_with_emails:
            if parent_with_email['products_count'] == 1:
                deals_with_products.append(parent_with_email)

        if deals_with_products.__len__() == 0:
            error = "No deal with only 1 product was found."
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

        # Get Student first name
        for deals_with_product in deals_with_products:
            if deals_with_product["88a0962f7916a41085bf8545f3b9433485140da5"] is not None:
                self.clean_deals.append(deals_with_product)

        if self.clean_deals.__len__() == 0:
            error = "No student with first name found"
            raise EdukaPipedriveNoDealsFoundException(self.service_name, self.school, error)

    def run(self, cmd: str):
        try:
            pipelines = []
            stages = []
            for pl in self.ask_pipedrive("pipeline"):
                pipelines.append(pl)
                # print(f"id: {pl['id']}, school name: {pl['name']}, url title: {pl['url_title']}, active: {pl[
                # 'active']}")

            # print(pipelines)

            # print(self.get_deals_from_stage_by_pipeline(161, "admitted"))
            self.check_conditions()
            print(self.clean_deals)
        except EdukaPipedriveNoDealsFoundException as e:
            print(str(e))
            self.error_logger.critical("Eduka Pipedrive Not Deals Found Exception occured", exc_info=True)
