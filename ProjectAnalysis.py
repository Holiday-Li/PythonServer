import os, logging
import xml.etree.ElementTree as ET


def get_ewp_file_path(project_path:str)->str:
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


def get_ewp_name(project_path:str, logger:logging.Logger)->str:
    # Get project config file
    proj_file_path = get_ewp_file_path(project_path)
    if not proj_file_path:
        logger.error("Could not found project config file.")
        logger.error("Project path: {}".format(project_path))
        return None
    
    # Get project name.
    project_path, proj_file_name = os.path.split(proj_file_path)
    ewp_name = proj_file_name[:proj_file_name.find(".ewp")]
    logger.info("Get ewp file name, name: {}".format(ewp_name))
    return ewp_name


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
    testStr = '"--jet_board_cfg=C:\\Users\\Administrator\\Documents\\02-SDK\\5_2_2\\emps_SLT_demo_20240402\\demos\\slt\\EWRISCV\\..\\..\\..\\IDE\\EWRISCV\\debugger\\ESWIN\\EAM2011.probeconfig" '
    key, value = parse_key_value_str(testStr)
    print("Key:{}".format(key))
    print("Value:{}".format(value))