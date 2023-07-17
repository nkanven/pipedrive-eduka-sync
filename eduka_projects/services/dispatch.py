import os

from eduka_projects.bootstrap import EdukaProjects

from eduka_projects.services.database_backup.backup_automation import Backup
from eduka_projects.services.code_manager.db_populate import Populate
from eduka_projects.services.code_manager.corrector import Correct
from eduka_projects.services.statistics.login import Login

loader = {
    "corrector": Correct,
    "db_populate": Populate,
    "backup_automation": Backup,
    "login": Login
}


def dispatcher(service_name: str, school: str):
    edkp = EdukaProjects()
    service = None
    services_dirs_path = edkp.base_dir + os.sep + "services"
    services_dirs: list = [files for files in os.listdir(services_dirs_path) if
                           os.path.isdir(os.path.join(services_dirs_path, files))]
    print(f"Program is searching for {service_name}...")
    try:

        for service_folder in services_dirs:
            if service_folder == "__pycache__":
                continue

            for service_file in os.listdir(os.path.join(services_dirs_path, service_folder)):
                service_file_dic = service_file.split(".")
                print(service_name, service_file_dic)

                print(service_name in service_file_dic)
                if service_name in service_file_dic:
                    service = service_file_dic[0]

                    _service = loader[service](school)
                    print("running ", service)
                    _service.run(service_name)
                    break
        if service is None:
            print(f"{service} not found. Please check the command orthograph or contact the admin.")
        else:
            print(f"{service} has been successfully executed. Check out your e-mail for notification summary")
    except Exception as e:
        edkp.error_logger.critical("Exception occured", exc_info=True)
