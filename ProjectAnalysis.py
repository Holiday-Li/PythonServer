import os, logging
import xml.etree.ElementTree as ET


def get_ewp_path_list(project_path:str)->list:
    path_list = []
    for root, _, files in os.walk(project_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path.find("example") != -1:
                continue
            elif file_path.find("template") != -1:
                continue
            if file_path.find(".ewp") != -1:
                path_list.append(file_path)
    return path_list


def get_ewp_name(project_path:str, logger:logging.Logger)->str:
    # Get project config file
    ewp_path_list = get_ewp_path_list(project_path)
    if len(ewp_path_list) != 1:
        logger.error("Not only one ewq file exist.")
        for ewp_path in ewp_path_list:
            logger.error("ewp file: {}".format(ewp_path))
        logger.error("Project path: {}".format(project_path))
        return None
    ewp_path = ewp_path_list[0]
    
    # Get project name.
    project_path, proj_file_name = os.path.split(ewp_path)
    ewp_name = proj_file_name[:proj_file_name.find(".ewp")]
    logger.info("Get ewp file name, name: {}".format(ewp_name))
    return ewp_name

# Get custom argvars file path list in this project
def get_ca_path_list(project_path:str)->list:
    path_list = []
    for root, _, files in os.walk(project_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path.find("example") != -1:
                continue
            elif file_path.find("template") != -1:
                continue
            if file_path.find(".custom_argvars") != -1:
                path_list.append(file_path)
    return path_list


def get_core_arch(ewp_file_path:str, logger:logging.Logger)->str:
    tree = ET.parse(ewp_file_path)
    root = tree.getroot()

    sub_node = root.find("configuration").find("toolchain").find("name")
    try:
        core_arch = sub_node.text
    except:
        logger.error("No toolchain found, please check the xml file.")
        core_arch = None
    return core_arch


def parse_key_value_str(kv_str:str)->tuple[str, str]:
    equal_sign_cnt = kv_str.count("=")
    if equal_sign_cnt != 1:
        return "", ""
    str_list = kv_str.split("=")
    key = str_list[0]
    value = str_list[1]
    return key, value


def get_file_base_in_project(project_path:str, file_name:str)->str:
    base_path = ""
    for root, _, files in os.walk(project_path):
        if base_path:
            break
        for file in files:
            if file == file_name:
                base_path = root
                break
    return base_path

if __name__ == "__main__":
    print("Test start")
    project_path = "F:\\Work\\NECV\\E360\\E3_SSDK_PTG3.0_Source_Code\\ssdk"
    print("ProjectPath: {}".format(project_path))
    ca_list = get_ca_path_list(project_path=project_path)
    print("---Result---")
    for ca_file in ca_list:
        print("Custom argvars file: {}".format(ca_file))