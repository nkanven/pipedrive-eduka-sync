"""
# PipeDrive Synchro Service

This service objective is to synchronize deals from PipeDrive to Eduka Platform, and from Eduka Platform to PipeDrive
"""
import requests
from eduka_projects.services import ServiceManager
from eduka_projects.utils.eduka_exceptions import EdukaPipedriveNoPipelineFoundException

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

        for key, value in kwargs.items():
            url += "&" + key + "=" + str(value)

        payload = {}
        headers = {
            'Accept': 'application/json'
        }

        session = self.get_session()
        response = session.get(url, headers=headers, data=payload)

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
