"""
# PipeDrive Synchro Service

This service objective is to synchronize deals from PipeDrive to Eduka Platform, and from Eduka Platform to PipeDrive
"""
import os
import time
import csv

import requests
from eduka_projects.services import ServiceManager
from eduka_projects.utils.rialization import serialize, deserialize
from eduka_projects.utils.eduka_exceptions import EdukaPipedriveNameParameterException

import json


class PipedriveService(ServiceManager):
    """
    Pipedrive service main class inherited ServiceManager
    """
    def __init__(self):
        super().__init__()
        self.pipedrive_params = self.parameters["global"]["pipedrive"]
        self.product_fname = "pipedriveproducts.ep"
        self.product_path = os.path.join(self.autobackup_memoize, self.product_fname)
        self.genders = {"male": 102, "female": 103, "garçon": 102, "fille": 103}
        self.genders_to_eduka = {102: "G", 103: "F"}
        self.get_pipedrive_param_name_for = {
            "student id": "0dfe2a7c991908de1eb76779d5a99487c3955f9b",
            "student first name": "88a0962f7916a41085bf8545f3b9433485140da5",
            "student last name": "525ad777ef8851736fd9a46986d5c5c26541fdc5",
            "gender": "f138752f358c149c11bce02f6003a718d36d3575",
            "parent first name": "dc4ec04f55ae86eab296ce0ada292a9237c77a35",
            "parent last name": "bb03d0847076fe0486020b79c21dc58b06b43251",
            "email": "f6bbcc60845993baedec912a5d4b2056d92fe5a8",
            "phone": "116182a46dd67c25cdd4ced5ec4f7d0ed1526f15",
            "product_code": "e33b8f35c28748baa1b2ee05980ca89c2588db1e"
        }

    def get_pipedrive_endpoint(self, point, endpoint_as_given=False)-> str:
        """
        Build pipedrive endpoint according to parameters received
        @param point: action to do
        @param endpoint_as_given: False to use point as it is. True if point need to be build to endpoint
        @return: (str) Pipedrive build endpoint
        """
        endpoint = point if endpoint_as_given else self.pipedrive_params["endpoints"][point]
        return self.pipedrive_params["base_url"] + endpoint + "?api_token=" + \
            self.pipedrive_params["api_token"]

    def post_to_pipedrive(self, endpoint, params, endpoint_as_given=False, method="POST") -> dict:
        """
        Post data to Pipedrive
        @param endpoint: endpoint url
        @param params: dict of parameters
        @param endpoint_as_given: do not modify point if True
        @param method: post method default to POST
        @return: dict response elements
        """
        url = self.get_pipedrive_endpoint(endpoint, endpoint_as_given)
        payload = json.dumps(params)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # exit(payload)
        response = requests.request(method, url, headers=headers, data=payload)

        return json.loads(response.text)

    def create_deal(self, data: dict) -> int:
        """
        Create deal to Pipedrive
        @param data: dict of data to post
        @return: int created deal ID
        """
        deal = self.post_to_pipedrive("deals", data)
        return deal["data"]["id"]

    def ask_pipedrive(self, endpoint, **kwargs) -> dict:
        """
        Pipedrive connector
        @param endpoint: endpoint url
        @param kwargs: arguments to post of get elemets from pipredrive
        @return: dict Response dictonary
        """
        url = self.get_pipedrive_endpoint(endpoint)

        path = ""

        for key, value in kwargs.items():
            if key == "path":
                path += f"/{value}"
                continue

            url += "&" + key + "=" + str(value)

        url = url.replace("?", f"{path}?") + "&limit=1000"
        print(url)

        payload = {}
        headers = {
            'Accept': 'application/json'
        }

        session = self.get_session()
        # response = session.get(url, headers=headers, data=payload)
        response = requests.get(url, headers=headers, data=payload)

        return json.loads(response.text)["data"]

    def add_product_to_a_deal(self, deal_id, product_id):
        """
        Add a product to a deal on Pipedrive
        @param deal_id: the Id of the deal to update
        @param product_id: the Id of the product to associate
        @return: void
        """
        endpoint = f"deals/{deal_id}/products"
        add_d_p = self.post_to_pipedrive(
            endpoint, {
                "product_id": product_id,
                "item_price": 0,
                "quantity": 1
            }, endpoint_as_given=True
        )
        print(f"Deal {deal_id} added to product responds {add_d_p}")

    def get_admitted_stage_id(self, pipeline_id, stage_name="admitted") -> int:
        """
        Get admitted stage Id of a pipeline
        @param pipeline_id: the pipeline ID
        @param stage_name: the stage name default to admitted
        @return: int the stage ID
        """
        stage_id = None
        stages = self.ask_pipedrive("stages", pipeline_id=pipeline_id)
        for stage in stages:
            if stage['name'].lower() == stage_name:
                stage_id = stage['id']

        return stage_id

    def get_deals_from_stage_by_pipeline(self, pipeline_id: int, stage_name: str) -> list:
        """
        Get all deals from a stage by pipeline
        @param pipeline_id: the pipeline ID
        @param stage_name: the stage name
        @return: list deals
        """
        deals = []
        stage_id = self.get_admitted_stage_id(pipeline_id, stage_name)
        print("stage id ", stage_id)
        if stage_id is not None:
            deals_call = self.ask_pipedrive("deals", stage_id=stage_id)
            if deals_call is not None:
                deals.append(deals_call)

        print("deals ", deals)

        return deals

    def get_product_code(self, deal_id):
        """
        Get a product code with deal ID
        @param deal_id: the deal ID
        @return: product
        """
        path = str(deal_id) + "/products/"
        product = self.ask_pipedrive("deals", path=path)
        return product

    def get_school_branch_code(self, product_id):
        """
        Get the school branch code with a prodcut ID
        @param product_id: the product ID
        @return: school branch code
        """
        path = f"products/{product_id}"
        school_bcode = None
        product = self.ask_pipedrive("products", path=product_id)

        if product is not None:
            school_bcode = product["639757ba26481440820c9b29d205bba9ba25dcb2"]
        return school_bcode

    def get_deals_from_stage_by_pipelines(self, pipeline_ids: list, stage_name: str) -> list:
        """
        Get deals from stage with pipelines
        @param pipeline_ids: the pipelines ID list
        @param stage_name: the stage name
        @return: list of deals
        """
        deals = []
        try:
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
        """
        Create excel file to import on Eduka
        @param file_name: csv file name
        @param heads: head
        @param content: csv content
        @return: void
        """
        with open(f'{file_name}.csv', "w") as f:
            write = csv.writer(f, delimiter=",")
            write.writerow(heads)
            write.writerows(content)

    def get_family_id(self, abbr, base_url, school, parent_email):
        """
        Get family ID from guardian list on Eduka platform
        @param abbr: school abbreviation
        @param base_url: Eduka school base url
        @param school: school name
        @param parent_email: parent email address
        @return: int family ID
        """
        fam_id = None
        family_ids = self.get_guardians(abbr, base_url, school)

        for family_id in family_ids:
            if family_id[2] == parent_email:
                fam_id = family_id[0]

        return fam_id

    def get_products(self):
        """
        get all products for Pipedrive and store them
        @return:
        """
        if os.path.exists(self.product_path):
            products = deserialize(self.autobackup_memoize, self.product_fname)
        else:
            products = self.ask_pipedrive("products")
            serialize(self.product_path, products)

        return products

    def delete_product_memo(self):
        """
        Delete product memoization
        @return: void
        """
        try:
            os.remove(self.product_path)
        except FileNotFoundError:
            pass

    def get_product_id_from_school_code(self, school_code: str) -> int:
        """
        Get product ID from given school code
        @param school_code: the school code
        @return: int product id
        """
        product_id = None

        for product in self.get_products()[0]:
            try:
                if product[self.get_pipedrive_param_name_for["product_code"]] == school_code:
                    product_id = product["id"]
                    break
            except TypeError:
                pass

        return product_id

    def get_pipeline_with_product_id(self, product_id, school):
        """
        Get pipeline with a product ID
        @param product_id: the product ID
        @param school: school name
        @return: int pipeline ID
        """
        pipelines = self.get_school_parameter(school, "pipedrive_pipelines")
        pipeline_id = None
        for key, value in pipelines.items():
            if str(product_id) in value['productID_list'].split(","):
                pipeline_id = key
                break
        return pipeline_id

    def update_deal(self, deal_id, params: dict):
        """
        Update a deal
        @param deal_id: deal ID
        @param params: dict parameters
        @return: void
        """
        endpoint = f"deals/{deal_id}"
        update_d = self.post_to_pipedrive(endpoint, params, endpoint_as_given=True, method="PUT")
        print(f"Update deal responds {update_d}")
