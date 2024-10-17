from datetime import datetime
import multiprocessing.managers
import os, sys
import shutil
import subprocess
import time
import multiprocessing, logging
from ProjectAnalysis import get_ewp_name, get_ewp_path_list, get_ca_path_list, get_core_arch, get_file_base_in_project, parse_key_value_str
from Utils import get_current_dir_path
from Logger import get_logger, clean_log_files
from ProjectDBAccess import get_project_path, get_ide_path, get_node_name, get_compile_cfg, get_test_type


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
    logger.info("ProjectPath: {}".format(project_path))
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
    # os.rename(target_file_path, backup_file_name)
    shutil.copy(target_file_path, backup_file_name)
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
    else:
        logger.error("Cound not find target file.")
        return False

    template_file_path = get_template_file_path(logger)
    if not template_file_path:
        logger.error("Get template file path error.")
        return False

    test_node_name = get_node_name(project_id=project_id, module_id=module_id, sub_id=sub_id, logger=logger)
    if not test_node_name:
        logger.error("Get test node name error.")
        return False
    
    test_type = get_test_type(project_id=project_id, logger=logger)
    if not test_type:
        logger.error("Get test type error.")
        return False

    work_file_path = target_file_path + "_working"
    shutil.copy(template_file_path, work_file_path)
    with open(work_file_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.find("%task_name%") != -1:
            new_lines.append(line.replace("%task_name%", test_node_name))
        elif line.find("%proc_function%") != -1:
            if test_type == "CanTrigger":
                new_lines.append(line.replace("%proc_function%", "ProcByCmd()"))
            elif test_type == "AutoProc":
                new_lines.append(line.replace("%proc_function%", "ProcBySeq()"))
            else:
                logger.error("Invalid test_type.")
        else:
            new_lines.append(line)

    with open(work_file_path, "w") as f:
        f.writelines(new_lines)

    os.remove(target_file_path)
    os.rename(work_file_path, target_file_path)
    logger.info("Target file generate done, path: {}".format(target_file_path))
    return True


def env_set_up(project_id:int, logger:logging.Logger):
    # Get compile and download tool saved path by accessing database
    ide_path = get_ide_path(project_id, logger)
    tool_path = "{}\\common\\bin".format(ide_path)

    logger.info("Setup env path: {}".format(tool_path))
    os.environ['PATH'] = os.pathsep.join([tool_path, os.environ['PATH']])
    return


def project_build(project_id:int, logger:logging.Logger, compile_config:str="Debug")->bool:
    project_path = get_project_path(project_id=project_id, logger=logger)
    if not project_path:
        logger.error("Can not find project path, project_id:{}".format(project_id))
        return False
    # Find ewp config file
    ewp_path_list = get_ewp_path_list(project_path)
    if len(ewp_path_list) != 1:
        logger.error("Can not find *.ewp file.")
        return False
    ewp_file_path = ewp_path_list[0]

    # Find custom argvars config file
    ca_path_list = get_ca_path_list(project_path)
    if len(ca_path_list) > 1:
        logger.error("Found more than 1 custom_argvars file exist, please have a check.")
        return False
    elif len(ca_path_list) == 1:
        ca_path = ca_path_list[0]
    else:
        ca_path = None

    # Generate build command
    cmd = "iarbuild " + ewp_file_path + " -make " + compile_config
    if ca_path:
        cmd = cmd + " -varfile " + ca_path
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
    if not ewp_name:
        return False
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


def get_target_file_in_ide(target_file:str, ide_path:str, logger:logging.Logger)->str:
    target_file_path = ""
    for root, _, files in os.walk(ide_path):
        if target_file_path:
            break
        for file in files:
            if file != target_file:
                continue
            target_file_path = os.path.join(root, file)
            logger.info("Found target file - {}, path:{}".format(target_file, target_file_path))
            break
    return target_file_path


def get_proc_path_in_ide(core_arch:str, ide_path:str, logger:logging.Logger)->str:
    if core_arch == "RISCV":
        proc_dll = "riscvproc.dll"
    elif core_arch == "ARM":
        proc_dll = "armproc.dll"
    else:
        logger.error("Invalid core architecture.")
        return False
    proc_path = get_target_file_in_ide(target_file=proc_dll, ide_path=ide_path, logger=logger)
    if not proc_path:
        logger.error("Could not found proc dll file - *{}*".format(proc_dll))
    return proc_path


def get_jet_path_in_ide(core_arch:str, ide_path:str, logger:logging.Logger)->str:
    if core_arch == "RISCV":
        jet_dll = "riscvijet.dll"
    elif core_arch == "ARM":
        jet_dll = "armjlink.dll"
    else:
        logger.error("Invalid core architecture.")
        return False
    jet_path = get_target_file_in_ide(target_file=jet_dll, ide_path=ide_path, logger=logger)
    if not jet_path:
        logger.error("Could not found jet dll file - *{}*".format(jet_dll))
    return jet_path


def get_orignal_loader_path(orignal_file:str)->str:
    with(open(orignal_file, "r+")) as fp:
        lines = fp.readlines()
    loader_path = ""
    value = ""
    for line in lines:
        if line.find("--flash_loader") != -1:
            _, value = parse_key_value_str(line)
            break
    if value:
        loader_path = value.replace('"', '')
    return loader_path


def get_orignal_output_path(orignal_file:str)->str:
    with(open(orignal_file, "r+")) as fp:
        lines = fp.readlines()
    output_path = ""
    for line in lines:
        if line.find("Exe") != -1:
            output_path = line.replace("\n", "").replace(" ", "").replace('"', '')
    return output_path


def get_output_path(project_path:str, orignal_file:str, logger:logging.Logger)->str:
    orignal_output_path = get_orignal_output_path(orignal_file)
    if not orignal_output_path:
        logger.error("Could not found output path in orignal file - *{}*".format(orignal_file))
        return ""
    _, output_file = os.path.split(orignal_output_path)

    base_path = ""
    for root, dirs, _ in os.walk(project_path):
        if base_path:
            break
        for dir in dirs:
            if dir != "Exe":
                continue
            temp_path = os.path.join(root, dir)
            relative_path = temp_path[len(project_path):]
            logger.info("Output relative path: {}".format(relative_path))
            if orignal_output_path.find(relative_path) != -1:
                base_path = temp_path
                logger.info("Found output base path, path:{}".format(base_path))
                break
    if not base_path:
        logger.error("Could not found base path in project_path")
        logger.error("ProjectPath:{}".format(project_path))
        logger.error("OutputName:{}".format(output_file))
        return ""
    output_path = os.path.join(base_path, output_file)
    return output_path


def get_orignal_loader_path(orignal_file:str)->str:
    with(open(orignal_file, "r+")) as fp:
        lines = fp.readlines()
    loader_path = ""
    for line in lines:
        if line.find("--flash_loader") != -1:
            _, value = parse_key_value_str(line)
            loader_path = value.replace("\n", "").replace(" ", "").replace('"', '')
    return loader_path


def get_flashloader_path(project_path:str, orignal_file:str, logger:logging.Logger)->str:
    orignal_loader_path = get_orignal_loader_path(orignal_file)
    if not orignal_loader_path:
        logger.error("Could not found orignal loader path - {}".format(orignal_file))
        return ""

    loader_path = ""
    for root, _, files in os.walk(project_path):
        if loader_path:
            break
        for file in files:
            if file.find(".board") == -1 or root.find("flashloader") == -1:
                continue
            temp_path = os.path.join(root, file)
            relative_path = temp_path[len(project_path):]
            logger.info("flashloader relative path: {}".format(relative_path))
            if orignal_loader_path.find(relative_path) != -1:
                loader_path = temp_path
                break
    return loader_path


def get_plugin_path_in_ide(core_arch:str, ide_path:str, logger:logging.Logger)->str:
    if core_arch == "RISCV":
        plugin_dll = "riscvbat.dll"
    elif core_arch == "ARM":
        plugin_dll = "armLibsupportUniversal.dll"
    else:
        logger.error("Invalid core architecture.")
        return False
    plugin_path = get_target_file_in_ide(target_file=plugin_dll, ide_path=ide_path, logger=logger)
    if not plugin_path:
        logger.error("Could not found plugin dll file - *{}*".format(plugin_dll))
    return plugin_path


def general_xcl_file_generate(project_path:str, ide_path:str, logger:logging.Logger, compile_config:str="Debug")->bool:
    file_name = "auto_download.general.xcl"
    ewp_name = get_ewp_name(project_path, logger)
    orignal_file_name = "{project_name}.{compile_config}.general.xcl".format(
        project_name=ewp_name, compile_config=compile_config)

    base_path = get_file_base_in_project(project_path=project_path, file_name=orignal_file_name)
    if not base_path:
        logger.error("Could not find base path, orignal file - *{}*".format(orignal_file_name))
        return False

    file_path = os.path.join(base_path, file_name)
    if os.path.exists(file_path):
        logger.info("General xcl file already exist, path: {}".format(file_path))
        os.remove(file_path)

    ewp_path_list = get_ewp_path_list(project_path)
    if len(ewp_path_list) != 1:
        logger.error("Could not find *.ewp file.")
        return False
    ewp_file_path = ewp_path_list[0]
    
    core_arch = get_core_arch(ewp_file_path=ewp_file_path, logger=logger)
    logger.info("CoreArch: {}".format(core_arch))

    logger.info("Search target files in IDE: {}".format(ide_path))
    proc_path = get_proc_path_in_ide(core_arch=core_arch, ide_path=ide_path, logger=logger)
    if not proc_path:
        return False
    jet_path = get_jet_path_in_ide(core_arch=core_arch, ide_path=ide_path, logger=logger)
    if not jet_path:
        return False
    plugin_path = get_plugin_path_in_ide(core_arch=core_arch, ide_path=ide_path, logger=logger)
    if not plugin_path:
        return False

    orignal_file_path = os.path.join(base_path, orignal_file_name)
    output_path = get_output_path(project_path=project_path, orignal_file=orignal_file_path, logger=logger)
    if not output_path:
        return False
    flashloader_path = get_flashloader_path(project_path=project_path, orignal_file=orignal_file_path, logger=logger)

    lines = []
    lines.append('"{}" \n\n'.format(proc_path))
    lines.append('"{}" \n\n'.format(jet_path))
    lines.append('"{}" \n\n'.format(output_path))
    lines.append('--plugin="{}" \n\n'.format(plugin_path))
    if flashloader_path:
        lines.append('--flash_loader="{}" \n\n'.format(flashloader_path))

    with(open(file_path, "w+")) as fp:
        fp.writelines(lines)

    logger.info("General xcl file has been generated.")
    return True


def xcl_file_generator(project_id:int, compile_cfg:str, logger:logging.Logger)->bool:
    project_path = get_project_path(project_id, logger)
    if not project_path:
        return False
    ide_path = get_ide_path(project_id, logger)
    if not ide_path:
        return False
    ret = driver_xcl_file_generate(project_path, logger, compile_config=compile_cfg)
    if not ret:
        return ret
    ret = general_xcl_file_generate(project_path, ide_path, logger, compile_config=compile_cfg)
    return ret


def kill_running_process(sub_proc="CSpyBat.exe")->str:
    cmd = "tasklist | findstr {}".format(sub_proc)
    ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    if ret.stderr:
        return ret.stderr
    if ret.stdout.find(sub_proc) != -1:
        cmd = "taskkill /f /im {}".format(sub_proc)
        ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
        if ret.stderr:
            return ret.stderr
    return ""



def img_download(project_id:int, logger:logging.Logger, compile_config="Debug")->bool:
    err_msg = kill_running_process("CSpyBat.exe")
    if err_msg:
        logger.error("Kill CSpyBat error, err_msg:{}".format(err_msg))
        return False
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
    if compile_config == "Debug":
        cmd = ("cspybat -f " + general_config_path + " --backend -f " + driver_config_path)
    else:
        cmd = ("cspybat -f " + general_config_path + " --download_only --backend -f "
               + driver_config_path)
    # '''
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
    message = {
        "status": "Running",
        "timestamp": time.time()
    }
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    code_path = get_project_path(project_id, logger)
    if not code_path:
        message = {"status": "Error"}
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    # Step 2: Get IDE saved path
    ide_path = get_ide_path(project_id, logger)
    if not ide_path:
        message = {"status": "Error"}
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    # Step 2: Using template file to generate main.c
    message = {
        "status": "Running",
        "timestamp": time.time()
    }
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    ret = main_file_generate(project_id, module_id, sub_id, logger)
    if not ret:
        message = {"status": "Error"}
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    # Step 3: Generate xcl config files
    message = {
        "status": "Running",
        "timestamp": time.time()
    }
    compile_config = get_compile_cfg(project_id=project_id, logger=logger)
    ret = xcl_file_generator(project_id, compile_config, logger)
    if not ret:
        message = {"status": "Error"}
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    env_set_up(project_id, logger)
    # Step 3: Build image
    message = {
        "status": "Compiling",
        "timestamp": time.time()
    }
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    ret = project_build(project_id, logger, compile_config)
    if not ret:
        message = {"status": "Error"}
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return
    
    # Step 4: Download image to DUT
    message = {
        "status": "Debugging",
        "timestamp": time.time()
    }
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    ret = img_download(project_id=project_id, logger=logger, compile_config=compile_config)
    if not ret:
        message = {"status": "Error"}
        update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
        del logger
        return

    message = {"status": "Done"}
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    del logger
    return


def clean_build_image(project_id:int, compile_cfg:str, logger:logging.Logger):
    env_set_up(project_id=project_id, logger=logger)
    project_path = get_project_path(project_id=project_id, logger=logger)
    ewp_path_list = get_ewp_path_list(project_path)
    if len(ewp_path_list) != 1:
        logger.error("Can not find *.ewp file.")
        return False
    ewp_file_path = ewp_path_list[0]
    cmd = "iarbuild " + ewp_file_path + " -clean {}".format(compile_cfg)
    logger.info("Command:{}".format(cmd))
    ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    logger.info("Output:{}".format(ret.stdout))
    logger.info("ErrMsg:{}".format(ret.stderr))
    return


def E360_test():
    clean_log_files()
    logger = get_logger("E3640_Test")
    project_id = 2
    code_path = get_project_path(project_id, logger)
    if not code_path:
        logger.error("get_project_path error.")
        return

    ide_path = get_ide_path(project_id, logger)
    if not ide_path:
        logger.error("get_ide_path error.")
        return
    
    module_id = "MODULE_ID_SM4"
    # module_id = "MODULE_ID_RSA"
    sub_id = "0x0001"
    ret = main_file_generate(project_id, module_id, sub_id, logger)
    if not ret:
        logger.error("main_file_generate error.")
        return
    
    compile_config = get_compile_cfg(project_id=project_id, logger=logger)
    ret = xcl_file_generator(project_id, compile_config, logger)
    if not ret:
        logger.error("xcl_file_generator error.")
        return
    
    env_set_up(project_id, logger)
    # clean_build_image(project_id=project_id, compile_cfg=compile_config, logger=logger)

    # '''
    ret = project_build(project_id, logger, compile_config)
    if not ret:
        logger.error("project_build error.")
        return
    # '''
    ret = img_download(project_id=project_id, logger=logger, compile_config=compile_config)
    if not ret:
        logger.error("img_download error.")
        return


def file_copy_test():
    target_file_path = "F:\\Work\\VS_Code\\Python\\AutoCompileAndDownload\\template.c"
    logger = get_logger("copy_test")
    backup_target_file(target_file_path, logger)


if __name__ == "__main__":
    # E360_test()
    file_copy_test()