import git, os, logging
from git.exc import InvalidGitRepositoryError
from Logger import get_logger, clean_log_files
from ProjectDBAccess import get_code_source, get_project_name, get_project_path, set_project_path
from Utils import get_config_info

def clone_code(project_id:int, base_dir:str, logger:logging.Logger)->bool:
    #Get project name and generate project path by it.
    project_name = get_project_name(project_id=project_id, logger=logger)
    code_folder = os.path.join(base_dir, project_name)

    # If the code folder already exists,
    # it means that there are some project has the same name with this project.
    try:
        os.makedirs(code_folder)
    except FileExistsError:
        logger.error("The code folder has already exists, please keep the project_name is unique.")
        return False

    code_source = get_code_source(project_id=project_id, logger=logger)
    git.Repo.clone_from(code_source, code_folder)
    # After clone, update the code path to Database
    return set_project_path(project_id=project_id, project_path=code_folder, logger=logger)


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
    # If the project_path is "",
    # it means that the code has not been cloned from the remote repo,
    # So, it should clone the code first.
    if not project_path:
        config_info = get_config_info(logger=logger)
        base_path = config_info["base_path"]
        ret = clone_code(project_id=project_id, base_dir=base_path, logger=logger)
        if not ret:
            logger.error("Code clone error.")
            return False
    
    try:
        repo = git.Repo(project_path)
    except InvalidGitRepositoryError:
        logger.error("Invalide project path: {}".format(project_path))
        return False
    
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


if __name__ == "__main__":
    clean_log_files()
    logger=get_logger("GitTest")
    '''
    config_info = get_config_info(logger=logger)
    # clone_code(project_id=5, base_dir=config_info["base_path"], logger=logger)
    ret = update_code(project_id=6, logger=logger)
    print("Process result:{}".format(ret))
    '''
    project_path = get_project_path(project_id=6, logger=logger)
    repo = git.Repo(project_path)
    # '''
    origin_id = get_commit_id(project_path=project_path, logger=logger)
    #origin_id = "a893b2b25fc03c6bcc7d9e631d976db682eeb5d5"
    new_commit_id = "962ede1d32bc85e4e990996dacc667d29b421855"
    ret = update_code(project_id=6, logger=logger, commit_id=new_commit_id)
    if not ret:
        print("update_code error")
        tmp_id = get_commit_id(project_path=project_path, logger=logger)
        print("Project commit id:{}".format(tmp_id))
        exit()
    check_commit_id = get_commit_id(project_path=project_path, logger=logger)
    if check_commit_id == new_commit_id:
        print("Test succeed")
        ret = update_code(project_id=6, logger=logger, commit_id=origin_id)
        if not ret:
            print("commit restore error")
            exit()
    # '''
    del logger
