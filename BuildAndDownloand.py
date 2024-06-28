from datetime import datetime
import multiprocessing.managers
import os
import shutil
import subprocess
import time
import multiprocessing, logging
from ProjectAnalysis import get_ewp_name, get_ewp_file_path, get_core_arch, get_file_base_in_project, parse_key_value_str
from Utils import get_current_dir_path
from Logger import get_logger
from ProjectDBAccess import get_project_path, get_ide_path, get_node_name


'''
 * Function name: update_queue_message
 * Description: Update process status into message queue.
 * Input:
    lock - process lock
    msg_queue - Message queue between process tool and cmd process.
    message - The new message need to be updated
 * Output: Null
'''
def update_queue_message(msg_queue:multiprocessing.Queue, message:str,
                         lock:multiprocessing.Lock, logger:logging.Logger):
    if not msg_queue:
        logger.debug("[Message] {}".format(message))
        return
    lock.acquire()
    try:
        if msg_queue.empty():
            msg_queue.put(message)
        else:
            while not msg_queue.empty():
                msg_queue.get()
            msg_queue.put(message)
    finally:
        lock.release()
    return


'''
 * Function name: get_template_file_path
 * Description: Get the template file path
 * Input: Null
 * Output:
        Succeed - The template file path
        Fail - None
'''
def get_template_file_path(logger:logging.Logger)->str:
    dir_path = get_current_dir_path()
    logger.info("Current path:{}".format(dir_path))

    template_file_name = "template.c"
    file_path = os.path.join(dir_path, template_file_name)
    logger.info("Template file path:{}".format(file_path))

    if not os.path.exists(file_path):
        logger.error("Template file does not exist.")
        return None
    return file_path


def get_target_file_path(project_id:int, logger:logging.Logger)->str:
    project_path = get_project_path(project_id=project_id, logger=logger)
    if not project_path:
        logger.error("No project found, project_id={}".format(project_id))
        return None

    ewp_name = get_ewp_name(project_path=project_path, logger=logger)
    if not project_path:
        logger.error("Could not found the ewp name, project path={}".format(project_path))
        return None

    target_file_name = ewp_name + ".c"
    target_file_path = None
    for root, _, files in os.walk(project_path):
        for file in files:
            if file == target_file_name:
                target_file_path = os.path.join(root, file)
                break
        if target_file_path:
            break
    if not target_file_path:
        logger.error("Could not find targetFilePath.")
        logger.error("TargetFileName: {}".format(target_file_name))
        logger.error("ProjectPath: {}".format(project_path))
        return None
    logger.info("TargetFilePath:{}".format(target_file_path))
    return target_file_path


def backup_target_file(target_file_path:str, logger:logging.Logger):
    base_file_name, _ = os.path.splitext(target_file_path)
    backup_file_name = (base_file_name
                        + datetime.now().strftime("_%Y-%m-%d-%H-%M-%S")
                        + ".c")
    logger.info("Store target file to:{}".format(backup_file_name))
    os.rename(target_file_path, backup_file_name)
    return


'''
 * Function name: file_generate
 * Description: Get target test cases by module_id and sub_id, then generate target main.c
 * Input:
        code_path - target project code saved path
        module_id - test target module id
        sub_id - the test case id under this module
 * Output:
        Succeed - True
        Fail - False
'''
def main_file_generate(project_id:int, module_id:str, sub_id:str, logger:logging.Logger)->bool:
    target_file_path = get_target_file_path(project_id, logger)
    if target_file_path and os.path.exists(target_file_path):
        logger.info("Target file already exists, need backup the old file.")
        backup_target_file(target_file_path, logger)

    template_file_path = get_template_file_path(logger)
    if not template_file_path:
        logger.error("Get template file path error.")
        return False

    test_node_name = get_node_name(module_id=module_id, sub_id=sub_id, logger=logger)
    if not test_node_name:
        logger.error("Get test node name error.")
        return False
    
    work_file_path = target_file_path + "_working"
    shutil.copy(template_file_path, work_file_path)
    with open(work_file_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.find("%task_name%") != -1:
            new_lines.append(line.replace("%task_name%", test_node_name))
        else:
            new_lines.append(line)

    with open(work_file_path, "w") as f:
        f.writelines(new_lines)

    os.rename(work_file_path, target_file_path)
    logger.info("Target file generate done, path: {}".format(target_file_path))
    return True


def env_set_up(project_id:int, logger:logging.Logger):
    # Get compile and download tool saved path by accessing database
    ide_path = get_ide_path(project_id, logger)
    tool_path = "{}\\common\\bin".format(ide_path)

    logger.info("Setup env path: {}".format(tool_path))
    os.putenv("path", tool_path)
    return


def project_build(project_id:int, logger:logging.Logger, compile_config:str="Debug")->bool:
    project_path = get_project_path(project_id=project_id, logger=logger)
    if not project_path:
        logger.error("Can not find project path, project_id:{}".format(project_id))
        return False
    ewp_file_path = get_ewp_file_path(project_path)
    if not ewp_file_path:
        logger.error("Can not find *.ewp file.")
        return False
    cmd = "iarbuild " + ewp_file_path + " -make " + compile_config
    logger.info("Command:{}".format(cmd))
    ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    logger.info("Output:{}".format(ret.stdout))
    if ret.stderr:
        logger.info("ErrMsg:{}".format(ret.stderr))
        return False
    return True


def driver_xcl_file_generate(project_path:str, logger:logging.Logger, compile_config:str="Debug")->bool:
    file_name = "auto_download.driver.xcl"
    ewp_name = get_ewp_name(project_path, logger)
    orignal_file_name = ewp_name + "." + compile_config + ".driver.xcl"

    base_path = get_file_base_in_project(project_path=project_path, file_name=orignal_file_name)
    if not base_path:
        logger.error("Could not found original driver xcl file.")
        return False
    orignal_path = os.path.join(base_path, orignal_file_name)
    new_path = os.path.join(base_path, file_name)
    logger.debug("Orignal driver xcl file path: {}".format(orignal_path))
    logger.debug("Target will be generated at: {}".format(new_path))
    if os.path.exists(new_path):
        logger.info("Target file already exists, path: {}".format(new_path))
        os.remove(new_path)
    
    new_lines = []
    with(open(orignal_path, "r")) as orignal_fp:
        lines = orignal_fp.readlines()
        for line in lines:
            if line.find(".ddf") != -1:
                file_path = line.replace('"', '').replace("\n", "").replace(" ", "")
                logger.info("Found *.ddf file, path: {}".format(file_path))
                _, file_name = os.path.split(file_path)
                file_base = get_file_base_in_project(project_path=project_path, file_name=file_name)
                if not file_base:
                    logger.error("Could not found *.ddf file in project.")
                    logger.error("ProjectPath:{}.".format(project_path))
                    new_lines.clear()
                    break
                new_file_path = os.path.join(file_base, file_name)
                new_lines.append('"' + new_file_path + '" \n')
            elif line.find(".probeconfig") != -1:
                line = line.replace('"', '').replace('\n', '').replace(" ", "")
                logger.info("Found *.probeconfig key value str, str:{}.".format(line))
                key, file_path = parse_key_value_str(kv_str=line)
                if not file_path:
                    logger.error("parse_key_value_str error, KV_Str:{}".format(line))
                    new_lines.clear()
                    break
                logger.info("Get *.probeconfig file path, path:{}.".format(file_path))
                _, file_name = os.path.split(file_path)
                logger.info("Found *.probeconfig file, name: {}".format(file_name))
                file_base = get_file_base_in_project(project_path=project_path, file_name=file_name)
                if not file_base:
                    logger.error("Could not found *.probeconfig file in project folder.")
                    logger.error("ProjectPath:{}.".format(project_path))
                    new_lines.clear()
                    break
                new_file_path = os.path.join(file_base, file_name)
                new_lines.append('"' + key + '=' + new_file_path + '" \n')
            else:
                new_lines.append(line)
    
    if not new_lines:
        return False
    with(open(new_path, "w+")) as new_fp:
        new_fp.writelines(new_lines)
    logger.info("Driver xcl file has been generated.")
    return True


def general_xcl_file_generate(project_path:str, ide_path:str, logger:logging.Logger, compile_config:str="Debug")->bool:
    file_name = "auto_download.general.xcl"
    ewp_name = get_ewp_name(project_path, logger)
    orignal_file_name = "{project_name}.{compile_config}.general.xcl".format(
        project_name=ewp_name, compile_config=compile_config)

    base_path = get_file_base_in_project(project_path=project_path, file_name=orignal_file_name)
    if not base_path:
        logger.error("Could not find base path.")
        return False

    file_path = os.path.join(base_path, file_name)
    if os.path.exists(file_path):
        logger.info("General xcl file already exist, path: {}".format(file_path))
        os.remove(file_path)

    ewp_file_path = get_ewp_file_path(project_path)
    if not ewp_file_path:
        logger.error("Could not find *.ewp file.")
        return False
    
    core_arch = get_core_arch(ewp_file_path=ewp_file_path, logger=logger)
    logger.info("CoreArch: {}".format(core_arch))
    if core_arch == "RISCV":
        proc_dll = "riscvproc.dll"
        jet_dll = "riscvijet.dll"
        plugin_dll = "riscvbat.dll"
    else:
        logger.error("Invalid core architecture.")
        return False
    
    proc_path = None
    jet_path = None
    plugin_path = None
    logger.info("Search target files in IDE: {}".format(ide_path))
    for root, _, files in os.walk(ide_path):
        for file in files:
            if file == proc_dll:
                if not proc_path:
                    proc_path = os.path.join(root, file)
                    logger.info("Found proc_path, path:{}".format(proc_path))
                else:
                    logger.info("ProcFile already exists.")
            elif file == jet_dll:
                if not jet_path:
                    jet_path = os.path.join(root, file)
                    logger.info("Found jet_path, path:{}".format(jet_path))
                else:
                    logger.info("JetPath already exists.")
            elif file == plugin_dll:
                if not plugin_path:
                    plugin_path = os.path.join(root, file)
                    logger.info("Found plugin_path, path:{}".format(plugin_path))
                else:
                    logger.info("PluginPath already exists.")
    output_path = None
    flashloader_path = None
    for root, dirs, files in os.walk(project_path):
        for dir in dirs:
            if dir == "Exe":
                if not output_path:
                    output_path = os.path.join(root, dir)
                    logger.info("Found output_path, path:{}".format(output_path))
        for file in files:
            if file.find(".board") != -1 and root.find("flashloader") != -1:
                if not flashloader_path:
                    flashloader_path = os.path.join(root, file)
                    logger.info("Found flashloader_path, path:{}".format(flashloader_path))


    orignal_file_path = os.path.join(base_path, orignal_file_name)
    logger.debug("Original general xcl file path: {}".format(orignal_file_path))
    output_file = None
    with(open(orignal_file_path, "r")) as fp:
        data_lines = fp.readlines()
        for data_line in data_lines:
            if data_line.find("Exe") != -1:
                logger.info("Orignal output path: *{}*".format(data_line))
                old_path = data_line.replace("\n", "").replace(" ", "").replace('"', '')
                _, output_file = os.path.split(old_path)
                logger.info("Output file: {}".format(output_file))
                break
    if not output_file:
        logger.error("Could not found orignal output file name.")
        return False
    lines = []
    lines.append('"{}" \n\n'.format(proc_path))
    lines.append('"{}" \n\n'.format(jet_path))
    lines.append('"{}\\{}" \n\n'.format(output_path, output_file))
    lines.append('--plugin="{}" \n\n'.format(plugin_path))
    lines.append('--flash_loader="{}" \n\n'.format(flashloader_path))

    with(open(file_path, "w+")) as fp:
        fp.writelines(lines)

    logger.info("General xcl file has been generated.")
    return True


def xcl_file_generator(project_id:int, logger:logging.Logger)->bool:
    project_path = get_project_path(project_id, logger)
    if not project_path:
        return False
    ide_path = get_ide_path(project_id, logger)
    if not ide_path:
        return False
    ret = driver_xcl_file_generate(project_path, logger)
    if not ret:
        return ret
    ret = general_xcl_file_generate(project_path, ide_path, logger)
    return ret


def img_download(project_id:int, logger:logging.Logger, compile_config="Debug")->bool:
    project_path = get_project_path(project_id=project_id, logger=logger)
    if not project_path:
        logger.error("Could not found project_path, project_id:{}".format(project_id))
        return False
    ewp_name = get_ewp_name(project_path=project_path, logger=logger)
    if not ewp_name:
        logger.error("Could not found ewp file")
        return False
    orignal_file_name = "{project_name}.{compile_config}.general.xcl".format(
        project_name=ewp_name, compile_config=compile_config)
    base_path = get_file_base_in_project(project_path=project_path, file_name=orignal_file_name)
    if not base_path:
        logger.error("Could not find base path.")
        return False
    # driver_config_file = project_name + "." + compile_config + ".driver.xcl"
    driver_config_file = "auto_download.driver.xcl"
    driver_config_path = os.path.join(base_path, driver_config_file)
    # general_config_file = project_name + "." + compile_config + ".general.xcl"
    general_config_file = "auto_download.general.xcl"
    general_config_path = os.path.join(base_path, general_config_file)

    '''
    cmd = ("cspybat -f " + general_config_path + " --download_only --backend -f "
           + driver_config_path)
    '''
    cmd = ("cspybat -f " + general_config_path + " --backend -f " + driver_config_path)
    logger.info("Command: {}".format(cmd))
    ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    logger.info("OutPut: {}".format(ret.stdout))
    if ret.stderr:
        logger.info("ErrMsg: {}".format(ret.stderr))
        if ret.stderr.find("ERROR:") != -1:
            return False
    return True


def project_build_and_download(task_params:dict, msg_queue:multiprocessing.Queue, lock:multiprocessing.Lock, task_id:str):
    task_name   = "task_{}".format(task_id)
    project_id  = task_params["project_id"]
    module_id   = task_params["module_id"]
    sub_id      = task_params["sub_id"]

    logger = get_logger(task_name)
    # Step 1: Get target project path
    message = time.time()
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    code_path = get_project_path(project_id, logger)
    if not code_path:
        message = "Error"
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    # Step 2: Get IDE saved path
    ide_path = get_ide_path(project_id, logger)
    if not ide_path:
        message = "Error"
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    # Step 2: Using template file to generate main.c
    message = time.time()
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    ret = main_file_generate(project_id, module_id, sub_id, logger)
    if not ret:
        message = "Error"
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    # Step 3: Generate xcl config files
    message = time.time()
    ret = xcl_file_generator(project_id, logger)
    if not ret:
        message = "Error"
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    env_set_up(project_id, logger)
    # Step 3: Build image
    message = time.time()
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    ret = project_build(project_id, logger)
    if not ret:
        message = "Error"
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return
    
    # Step 4: Download image to DUT
    message = time.time()
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    ret = img_download(project_id=project_id, logger=logger)
    if not ret:
        message = "Error"
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    message = "Done"
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    del logger
    return


def clean_build_image(project_id:int, logger:logging.Logger):
    env_set_up(project_id=project_id, logger=logger)
    project_path = get_project_path(project_id=project_id, logger=logger)
    ewp_file_path = get_ewp_file_path(project_path)
    if not ewp_file_path:
        logger.error("Can not find *.ewp file.")
        return False
    cmd = "iarbuild " + ewp_file_path + " -clean Debug"
    logger.info("Command:{}".format(cmd))
    ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    logger.info("Output:{}".format(ret.stdout))
    logger.info("ErrMsg:{}".format(ret.stderr))
    return