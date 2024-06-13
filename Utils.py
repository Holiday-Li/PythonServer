import os

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

def clean_log_files():
    base_path = get_current_dir_path()
    log_folder = os.path.join(base_path, "log\\")
    print("log folder path:{}".format(log_folder))
    print("log files:")
    for root, _, files in os.walk(log_folder):
        for file in files:
            log_file = os.path.join(root, file)
            print("\t{}".format(log_file))
            os.remove(log_file)
    return

if __name__ == "__main__":
    clean_log_files()