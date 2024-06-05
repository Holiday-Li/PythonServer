import os
import json
import logging
from ProjectAnalysis import get_project_name, get_core_arch, get_ewp_file_path, \
    get_compiler_downloader_path, get_project_test_cases

class DBAccesser:
    def __init__(self):
        # TBD, init the database access object
        # Using file replace database now.
        current_path = os.path.dirname(os.path.abspath(__file__))
        self.data_file_path = os.path.join(current_path, "project_info.txt")

    def __get_project_list(self):
        project_list = []
        if os.path.exists(self.data_file_path):
            with(open(self.data_file_path, "r")) as file:
                data = file.read()
                if len(data) == 0:
                    project_list = []
                else:
                    data_list = json.loads(data)
                    project_list = sorted(data_list, key=lambda data_list:data_list["id"])
        return project_list

    def __is_need_update(self, project_list, project_path):
        update_flag = True
        for project_info in project_list:
            if project_info["project_path"] == project_path:
                update_flag = False
                break
        return update_flag

    def __get_project_info(self, project_path, max_index):
        project_info = {}
        project_name = get_project_name(project_path=project_path)
        if not project_name:
            return None
        print("ProjectName:{}".format(project_name))

        ewp_path = get_ewp_file_path(project_path=project_path)
        if not ewp_path:
            return None
        print("ewpFilePath:{}".format(ewp_path))
        core_arch = get_core_arch(project_file_path=ewp_path)
        if not core_arch:
            return None
        print("CoreArch:{}".format(core_arch))

        compiler_path, downloader_path = get_compiler_downloader_path(project_path=project_path,
                                                                      core_arch=core_arch,
                                                                      project_name=project_name)
        if (not compiler_path) or (not downloader_path):
            return None
        print("compilerPath:{}".format(compiler_path))
        print("downloaderPath:{}".format(downloader_path))
        
        test_cases = get_project_test_cases(project_path=project_path)

        project_info["id"] = max_index + 1
        project_info["name"] = project_name
        project_info["project_path"] = project_path
        project_info["ewp_path"] = ewp_path
        project_info["core_arch"] = core_arch
        project_info["compiler"] = compiler_path
        project_info["downloader"] = downloader_path
        project_info["test_cases"] = test_cases
        return project_info

    def update_project_info(self, project_path):
        print("ProjectPath:\n{}".format(project_path))
        project_list = self.__get_project_list()
        print("Len of project_list:{}".format(len(project_list)))
        
        if not self.__is_need_update(project_list, project_path):
            return "Done"

        if not project_list:
            max_index = 0
        else:
            max_index = project_list[-1]["project_id"]
        project_info = self.__get_project_info(project_path, max_index)
        if not project_info:
            print("Could not found project")
            return "Done"

        project_list.append(project_info)
        with(open(self.data_file_path, "w+")) as file:
            data = json.dumps(project_list, indent=4)
            file.write(data)
        return "Done"

    def get_project_info(self, project_id):
        project_list = self.__get_project_list()
        for project_info in project_list:
            if project_info["id"] == project_id:
                return project_info
        return None
    
    def del_project_info(self, project_id):
        project_list = self.__get_project_list()
        for project_info in project_list:
            if project_info["id"] == project_id:
                project_list.remove(project_info)
                break

        with(open(self.data_file_path, "w+")) as file:
            data = json.dumps(project_list, indent=4)
            file.write(data)
        return


if __name__ == "__main__":
    project_path = ("C:\\Users\\lichunguang\\Documents\\WorkSpace\\"
                        "IAR_WorkSpace\\emps_SLT_demo_20240402")
    db_accesser = DBAccesser()
    db_accesser.update_project_info(project_path)

    project_info = db_accesser.get_project_info(project_id=1)
    project_info_str = json.dumps(project_info, indent=4)
    print("ProjectInfo:\n{}".format(project_info_str))

    db_accesser.del_project_info(project_id=1)
