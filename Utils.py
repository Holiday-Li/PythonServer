import os, logging

'''
 * Function name: get_current_dir_path
 * Description: Get the dir path which the running script saved.
 * Input: Null
 * Output: dir_path
'''
def get_current_dir_path():
    current_file_path = os.path.abspath(__file__)
    dir_path = os.path.dirname(current_file_path)
    return dir_path

config_info = {}

def get_config_info(logger:logging.Logger, config_file_path=None)->bool:
    global config_info
    if not config_file_path:
        base_path = get_current_dir_path()
        config_file_path = os.path.join(base_path, "config.cfg")
    if not os.path.exists(config_file_path):
        logger.error("config file does not exist")
        return False
    with(open(config_file_path, "r")) as fp:
        lines = fp.readlines()

    for line in lines:
        key, value = line.split("=")
        # print("Key:{}, Value:{}".format(key, value))
        config_info[key]=value.replace("\n", "")
    return True

def get_config_value(key:str, logger:logging.Logger)->str:
    global config_info
    if not config_info:
        get_config_info(logger)
    if key in config_info:
        return config_info[key]
    else:
        logger.error("No key in config_info, please check the config file.")
        logger.error("Key : {}".format(key))
        return ""

def get_code_base_path(logger:logging.Logger)->str:
    key = "code_base_path"
    return get_config_value(key=key, logger=logger)

def get_db_base_path(logger:logging.Logger)->str:
    key = "db_base_path"
    return get_config_value(key=key, logger=logger)

if __name__ == "__main__":
    from Logger import clean_log_files, get_logger
    clean_log_files()
    logger = get_logger("utils_test")
    code_base = get_code_base_path(logger)
    print("CodeBase:{}".format(code_base))
    db_base = get_db_base_path(logger)
    print("DB Base: {}".format(db_base))