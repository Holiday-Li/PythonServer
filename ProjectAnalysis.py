import os
import xml.etree.ElementTree as ET


def get_ewp_file_path(project_path):
    for root, _, files in os.walk(project_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path.find("example") != -1:
                continue
            elif file_path.find("template") != -1:
                continue
            if file_path.find(".ewp") != -1:
                return file_path
    return None


def get_project_name(project_path, logger):
    # Get project config file
    proj_file_path = get_ewp_file_path(project_path)
    if not proj_file_path:
        logger.error("Could not found project config file.")
        return None
    logger.info("Project config file path:\n{}".format(proj_file_path))
    
    # Get project name.
    project_path, proj_file_name = os.path.split(proj_file_path)
    project_name = proj_file_name[:proj_file_name.find(".ewp")]
    logger.info("Project Name: {}".format(project_name))
    return project_name


def get_core_arch(project_file_path):
    tree = ET.parse(project_file_path)
    root = tree.getroot()

    sub_node = root.find("configuration").find("toolchain").find("name")
    try:
        core_arch = sub_node.text
    except:
        print("No toolchain found, please check the xml file.")
        core_arch = None
    return core_arch


def get_compiler_downloader_path(project_path, core_arch, project_name):
    # Get general xcl file path
    dir_path, file_name = os.path.split(project_path)
    print("DirPath:{}".format(dir_path))
    print("FileName:{}".format(file_name))

    file_path = None
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.find("general.xcl") != -1:
                if file.find(project_name) == -1:
                    continue
                print("GenernalFileName:{}".format(file))
                print("Root:{}".format(root))
                file_path = os.path.join(root, file)
                break
    
    # In this case, the xcl file does not found.
    if not file_path:
        return None, None
    
    # Iterate over xcl file to find IDE path
    target_str = "{}\\bin".format(core_arch.lower())
    with(open(file_path, "r") as f):
        lines = f.readlines()
        for line in lines:
            if line.find(target_str) != -1:
                print("Got the target line.")
                print("Content:\n{}".format(line))
                break
    base_path = line[line.find('"') + 1 : line.find(target_str)] + "common\\bin\\"
    print("[INFO] Base path of IDE is:\n{}".format(base_path))
    compiler_path = os.path.join(base_path, "iarbuild.exe")
    print("[INFO] Compiler path:\n{}".format(compiler_path))
    if os.path.exists(compiler_path):
        print("[INFO] Compiler path found.")
    else:
        print("[ERROR] Compiler path could not found.")
    downloader_path = os.path.join(base_path, "CspyBat.exe")
    print("[INFO] Downloader path:\n{}".format(downloader_path))
    if os.path.exists(downloader_path):
        print("[INFO] Downloader path found.")
    else:
        print("[ERROR] Downloader path could not found.")
    return compiler_path, downloader_path


def get_tc_file_list(project_path):
    file_path_list = []
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.find("_module.c") != -1:
                file_path = os.path.join(root, file)
                file_path_list.append(file_path)
    flag = True
    for file_path in file_path_list:
        print(file_path)
        if not os.path.exists(file_path):
            flag = False
            break
    if not flag:
        return None
    return file_path_list


def get_value_by_assignment_str(assignment_str):
    index = assignment_str.find("=")
    length = len("=")
    return assignment_str[index + 1:].replace(" ", "").replace('"', "").replace(",", "").replace("\n", "")


def get_tc_info_by_tc_file(file_path):
    tc_list = []
    with (open(file_path, "r") as f):
        lines = f.readlines()
        for line in lines:
            if line.find("task_node_t") != -1:
                test_case = line[line.find("task_node_t") + len("task_node_t"):
                                 line.find("=")]
                test_case = test_case.replace(" ", "")
                start_index = lines.index(line)
                end_index = 0
                for tmp_line in lines[start_index:]:
                    if tmp_line.find("}") != -1:
                        end_index = start_index + lines.index(tmp_line)
                if end_index == 0:
                    print("Analysis error.")
                    return None

                for target_line in lines[start_index: end_index]:
                    if target_line.find("moduleId") != -1:
                        module_id = get_value_by_assignment_str(target_line)
                    elif target_line.find("subId") != -1:
                        sub_id = get_value_by_assignment_str(target_line)
                    elif target_line.find("taskName") != -1:
                        task_name = get_value_by_assignment_str(target_line)
                    elif target_line.find("taskProc") != -1:
                        task_proc = get_value_by_assignment_str(target_line)
                    else:
                        continue
                tc_dic = {
                    "testCase": test_case,
                    "moduleId": module_id,
                    "subId": sub_id,
                    "taskName": task_name,
                    "taskProc": task_proc,
                }
                tc_list.append(tc_dic)
    return tc_list


def get_project_test_cases(project_path):
    tc_list = []
    file_path_list = get_tc_file_list(project_path)

    for file_path in file_path_list:
        test_cases = get_tc_info_by_tc_file(file_path)
        for test_case in test_cases:
            tc_list.append(test_case)
    return tc_list