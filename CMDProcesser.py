import multiprocessing, os, time, logging
# from UDPServer import UDPServer
from TCPServer import TCPServer
import BuildAndDownloand
from GitProcesser import update_tc_code
from Logger import get_logger, clean_log_files

class CMDProcesser:
    # udp_server = None
    tcp_server = None

    def __init__(self, host="127.0.0.1", port=12345, max_task_count = os.cpu_count()):
        # The max process count for this object, using cpu core count as default
        self.max_task_count = max_task_count
        # Current running task count
        self.running_task_count = 0
        # The task_seq is used to marking task as task id
        self.task_seq = 0
        # Initialize the sub-process for command task information.
        self.task_list = []
        # Initialize UDP server object.
        # self.udp_server = UDPServer(host, port)
        self.tcp_server = TCPServer(host, port)

    def __del__(self):
        if self.tcp_server:
            del self.tcp_server

    def  request_analysis(self, request_data:str):
        param_list = request_data.split(" ")
        args = {}
        if param_list[0] == "exit":
            if len(param_list) == 1:
                cmd = param_list[0]
                args = None
            else:
                cmd = None
                args = None
        elif param_list[0] == "get_task_status":
            # Command format: get_task_status -t <task_id]>
            # Description: Get target task status to Upper monitor
            if (("-t" not in param_list) or
                (param_list.index("-t") != 1) or
                (len(param_list) != 3)):
                cmd = None
                args = None
            else:
                try:
                    args["task_id"] = param_list[2]
                    cmd = param_list[0]
                except:
                    cmd = None
                    args = None
        elif (param_list[0] == "update_tc_code"):
            # Command format: update_tc_code -p <project_id> [-c <commit_id>]
            # Description: Update test cases code to target commit id
            if (("-p" not in param_list) or
                (param_list.index("-p") != 1) or
                ((len(param_list) != 3) and len(param_list) != 5)):
                cmd = None
                args = None
            else:
                try:
                    args["project_id"] = int(param_list[2])
                    cmd = param_list[0]
                except:
                    cmd = None
                    args = None
                if cmd and len(param_list) == 5:
                    if param_list[3] != "-c":
                        cmd = None
                        args = None
                    elif param_list[4] != "NULL":
                        args["commit_id"] = param_list[4]
        elif (param_list[0] == "build_and_download"):
            # Command format: build_and_download -p <project_id> -m <module_id> -s <sub_id>
            # Description: Generate image and download to the DUT
            if (("-p" not in param_list) or (param_list.index("-p") == len(param_list))) or \
               (("-m" not in param_list) or (param_list.index("-m") == len(param_list))) or \
               (("-s" not in param_list) or (param_list.index("-s") == len(param_list))) or \
               (len(param_list) != 7):
                cmd = None
                args = None
            else:
                for index, value in enumerate(param_list):
                    if value == "-p":
                        try:
                            args["project_id"] = param_list[index + 1]
                        except:
                            args = None
                            break
                    elif value == "-m":
                        args["module_id"] = param_list[index + 1]
                    elif value == "-s":
                        try:
                            args["sub_id"] = param_list[index + 1]
                        except:
                            args = None
                            break
                if args:
                    cmd = param_list[0]
                else:
                    cmd = None
        else:
            cmd = None
            args = None
        return cmd, args
    

    def del_task(self, task_id):
        task_info = None
        for task_info in self.task_list:
            if task_id == task_info["task_id"]:
                break
        # If could not find the target task, return
        if not task_info or task_id != task_info["task_id"]:
            return
        # Release the resource of sub-process and message queue
        if task_info["process"]:
            while task_info["process"].is_alive():
                task_info["process"].terminate()
            task_info["process"].close()
        if task_info["msg_queue"]:
            task_info["msg_queue"].close()
        if task_info["lock"]:
            del task_info["lock"]
        self.task_list.remove(task_info)
        self.running_task_count -= 1
        return


    def get_task_status(self, task_id, logger:logging.Logger):
        logger.info("Get task status, task_id={}".format(task_id))
        task_id = task_id
        if len(self.task_list) == 0:
            logger.error("No task running.")
            return "None"
        # Get target task_info
        for task_info in self.task_list:
            if task_id == task_info["task_id"]:
                break
        # No target task found
        if task_info["task_id"] != task_id:
            logger.error("Could not found target task, task_id: {}".format(task_id))
            return "None"
        # Task found but no sub-process object
        # This situation means that some issue happened in new process allocation
        if not task_info["process"]:
            logger.error("The sub-process of task does not  exist, task_id: {}".format(task_id))
            return "Error"
        # The message of the task is empty
        if task_info["msg_queue"].empty():
            if not task_info["process"].is_alive():
                logger.error("Sub-process is not alive and the message queue is empty, task_id: {}".format(task_id))
                return "Error"
            # The sub-process is running but no new status updated
            if (time.time() - 300) > task_info["timestamp"]:
                logger.error("Task has not updated timestamp more than 5 mins, task_id: {}".format(task_id))
                return "Timeout"
            return task_info["status"]
        # The message queue is not empty, it means the sub-process has updated the status to the queue
        lock = task_info["lock"]
        lock.acquire()
        try:
            data = task_info["msg_queue"].get()
        finally:
            lock.release()
        if "timestamp" in data:
            task_info["timestamp"] = data["timestamp"]
            if (time.time() - 300) > data["timestamp"]:
                task_info["status"] = "Timeout"
            else:
                task_info["status"] = data["status"]
            logger.info("Task_{} timestamp: {}, status: {}".format(task_id, data["timestamp"], data["status"]))
        elif "status" in data:
            task_info["status"] = data["status"]
        else:
            logger.error("Unexpect error, task_id: {}".format(task_id))
        return task_info["status"]

    def alloc_process_for_task(self, cmd, func, task_params):
        if self.running_task_count == self.max_task_count:
            return -1
        
        msg_queue = multiprocessing.Queue()
        lock = multiprocessing.Lock()
        task_id = self.task_seq
        self.task_seq += 1
        params = (task_params, msg_queue, lock, task_id)
        process = multiprocessing.Process(target=func, args=params)
        process.start()
        task_info = {
            "task_id": str(task_id),
            "CMD": cmd,
            "task_params": task_params,
            "process": process,
            "msg_queue": msg_queue,
            "lock": lock,
            "timestamp": time.time(),
            "status": "Running"
        }
        self.task_list.append(task_info)
        self.running_task_count += 1
        return task_info["task_id"]


    def __start_build_and_download(self, project_id, module_id, sub_id):
        task_params = {
            "project_id": project_id,
            "module_id": module_id,
            "sub_id": sub_id,
        }
        task_id = self.alloc_process_for_task(cmd="build_and_download",
                                              func=BuildAndDownloand.project_build_and_download,
                                              task_params=task_params)
        return task_id

    def __update_project_code(self, project_id:int, commit_id:str):
        task_params = {
            "project_id": project_id,
            "commit_id": commit_id,
        }
        task_id = self.alloc_process_for_task(cmd="update_tc_code",
                                              func=update_tc_code,
                                              task_params=task_params)
        return task_id

    def start_service(self):
        clean_log_files()
        logger = get_logger("main_log")
        logger.info("Start listen.")
        while True:
            request_data, client_socket = self.tcp_server.get_request()
            logger.info("Get request: {}".format(request_data))
            cmd, args = self.request_analysis(request_data=request_data)
            if cmd == "exit":
                logger.info("CMD:{}".format(cmd))
                running_task_count = 0
                for task_info in self.task_list:
                    if task_info["process"].is_alive():
                        running_task_count += 1
                if running_task_count:
                    message = "Running"
                    self.tcp_server.send_response(client_socket, message)
                    logger.info("There has some task running, could not exit.")
                    continue
                message = "Done"
                self.tcp_server.send_response(client_socket, message)
                logger.info("exit CMD Processer")
                break
            elif cmd == "get_task_status":
                logger.info("CMD: {}".format(cmd))
                logger.info("task_id: {}".format(args["task_id"]))
                logger.info("TaskList:")
                for task_info in self.task_list:
                    logger.info("TaskInfo:{}".format(task_info))
                status = self.get_task_status(task_id=args["task_id"], logger=logger)
                logger.info("Task status: {}".format(status))
                if status == "Done" or status == "Error" or status == "Timeout":
                    logger.info("Task finished, need delete task information")
                    self.del_task(task_id=args["task_id"])
                self.tcp_server.send_response(client_socket, status)
            elif cmd == "update_tc_code":
                project_id = args["project_id"]
                if "commit_id" in args:
                    commit_id = args["commit_id"]
                else:
                    commit_id = ""
                logger.info("CMD: {}".format(cmd))
                logger.info("project_id: {}".format(project_id))
                logger.info("commit_id: {}".format(commit_id))
                task_id = self.__update_project_code(project_id=project_id, commit_id=commit_id)
                logger.info("TaskID: {}".format(task_id))
                self.tcp_server.send_response(client_socket, str(task_id))
                continue
            elif cmd == "build_and_download":
                logger.info("CMD: {}".format(cmd))
                logger.info("project_id: {}".format(args["project_id"]))
                logger.info("module_id: {}".format(args["module_id"]))
                logger.info("sub_id: {}".format(args["sub_id"]))
                task_id = self.__start_build_and_download(project_id=args["project_id"],
                                                           module_id=args["module_id"],
                                                           sub_id=args["sub_id"])
                logger.info("TaskID: {}".format(task_id))
                self.tcp_server.send_response(client_socket, str(task_id))
                continue
                # '''
            else:
                logger.info("Unexpect CMD:{}".format(request_data))
                message = "Error"
                self.tcp_server.send_response(client_socket, message)


if __name__ == "__main__":
    cmd_processer = CMDProcesser()
    cmd_processer.start_service()
    del cmd_processer