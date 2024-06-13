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

def get_config_info(logger:logging.Logger, config_file_path=None)->dict:
    config_info = {}
    if not config_file_path:
        config_file_path = ".\\config.cfg"
    if not os.path.exists(config_file_path):
        logger.error("config file does not exist")
        return None
    with(open(config_file_path, "r")) as fp:
        lines = fp.readlines()

    for line in lines:
        key, value = line.split("=")
        print("Key:{}, Value:{}".format(key, value))
        config_info[key]=value
    return config_info

if __name__ == "__main__":
    from Logger import clean_log_files, get_logger
    clean_log_files()
    logger = get_logger("utils_test")
    config_info = get_config_info(logger=logger)
    print("ConfigInfo: {}".format(config_info))
    print("BasePath:{}".format(config_info["base_path"]))