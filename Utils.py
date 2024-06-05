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