import git, os, logging, multiprocessing, time, shutil
from git.exc import InvalidGitRepositoryError
from Logger import get_logger, clean_log_files
from ProjectDBAccess import get_code_source, get_project_name, get_project_path, set_project_path, get_count_by_name
from Utils import get_code_base_path
from BuildAndDownloand import update_queue_message

def clone_code(project_name:str, base_dir:str, code_source:str, logger:logging.Logger)->bool:
    #Get project name and generate project path by it.
    code_folder = os.path.join(base_dir, project_name)

    # If the code folder already exists,
    # it means that there are some project has the same name with this project.
    if os.path.exists(code_folder):
        count = get_count_by_name(project_name=project_name, logger=logger)
        if count > 1:
            logger.error("The code folder has already exists, please keep the project_name is unique.")
            return ""
        shutil.rmtree(code_folder)

    os.makedirs(code_folder)

    try:
        git.Repo.clone_from(code_source, code_folder)
    except:
        logger.error("Code clone error, project_name:{}, code_folder:{}".format(project_name, code_folder))
        return ""
    return code_folder


def get_commit_id(project_path:str, logger:logging.Logger)->str:
    try:
        repo = git.Repo(project_path)
    except InvalidGitRepositoryError:
        logger.error("Invalide project path: {}".format(project_path))
        return None
    current_commit = repo.head.commit
    return current_commit.hexsha


def update_code(project_id:int, logger:logging.Logger, commit_id:str=None)->bool:
    project_path = get_project_path(project_id=project_id, logger=logger)
    logger.info("project_path:{}".format(project_path))
    if project_path:
        logger.info("ProjectPath exists:{}".format(os.path.exists(project_path)))
    # If the project_path is "",
    # it means that the code has not been cloned from the remote repo,
    # So, it should clone the code first.
    if (not project_path) or (not os.path.exists(project_path)):
        code_base = get_code_base_path(logger=logger)
        logger.info("CodeBase:{}".format(code_base))
        if not code_base:
            return False
        project_name = get_project_name(project_id=project_id, logger=logger)
        logger.info("ProjectName:{}".format(project_name))
        if not project_name:
            return False
        code_source = get_code_source(project_id=project_id, logger=logger)
        if not code_source:
            return False
        project_path = clone_code(project_name=project_name, base_dir=code_base,
                                  code_source=code_source, logger=logger)
        if not project_path:
            logger.error("Code clone error.")
            return False
        
        # After clone, update the code path to Database
        ret = set_project_path(project_id=project_id, project_path=project_path, logger=logger)
        if not ret:
            return ret
        logger.info("Clone code from git server, project_path:{}".format(project_path))
    
    try:
        repo = git.Repo(project_path)
    except InvalidGitRepositoryError:
        logger.error("Invalide project path: {}".format(project_path))
        return False
    repo.index.reset(index=True, working_tree=True)
    
    # If commit id is invalid, get the last version of the code.
    # else, change the code to the target commit.
    if not commit_id:
        repo.git.pull()
        return True
    else:
        repo.head.reset(commit_id)
        tmp_id = get_commit_id(project_path=project_path, logger=logger)
        if commit_id != tmp_id:
            logger.error("New commit id set error.")
            return False
        return True

def update_tc_code(task_params:dict, msg_queue:multiprocessing.Queue, lock:multiprocessing.Lock, task_id:str):
    project_id = task_params["project_id"]
    commit_id = task_params["commit_id"]
    logger = get_logger("task_{}".format(task_id))

    message = {
        "status": "Running",
        "timestamp": time.time()
    }
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)

    ret = update_code(project_id=project_id, logger=logger, commit_id=commit_id)
    if not ret:
        message = {"status": "Error"}
    else:
        message = {"status": "Done"}
    update_queue_message(msg_queue=msg_queue, message=message, lock=lock, logger=logger)
    return


def E3640_Test():
    clean_log_files()
    logger = get_logger("E3640_clone_test")
    project_id = 2
    ret = update_code(project_id=project_id, logger=logger)
    if not ret:
        logger.error("Clone error.")



if __name__ == "__main__":
    E3640_Test()