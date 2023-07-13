import os
from eduka_projects.bootstrap import Bootstrap
from eduka_projects.services.database_backup.backup_automation import Backup
from eduka_projects.services.code_manager.db_populate import Populate
from eduka_projects.services.code_manager.corrector import Correct
from eduka_projects.utils.mail import EnkoMail

loader = {
    "corrector": Correct,
    "db_populate": Populate,
    "backup_automation": Backup
}


class ServiceManager(Bootstrap):
    def __init__(self):
        print("Starting Service Manager (SM)...")
        super().__init__()
        self.services_dirs_path = self.base_dir + os.sep + "services"
        self.services_dirs: list = [files for files in os.listdir(self.services_dirs_path) if
                                    os.path.isdir(os.path.join(self.services_dirs_path, files))]

        print("SM, started")

    def dispatcher(self, service_name: str, school: str):
        service = None
        print(f"Program is searching for {service_name}...")
        try:

            for service_folder in self.services_dirs:
                if service_folder == "__pycache__":
                    continue

                for service_file in os.listdir(os.path.join(self.services_dirs_path, service_folder)):
                    service_file_dic = service_file.split(".")
                    print(service_name, service_file_dic)

                    print(service_name in service_file_dic)
                    if service_name in service_file_dic:
                        service = service_file_dic[0]

                        _service = loader[service](school)
                        print("running ", service)
                        _service.run()
                        break
            if service is None:
                print(f"{service} not found. Please check the command orthograph or contact the admin.")
            else:
                print(f"{service} has been successfully executed. Check out your e-mail for notification summary")
        except Exception as e:
            self.error_logger.critical("Exception occured", exc_info=True)
