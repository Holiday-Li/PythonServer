import multiprocessing
import os
import time
import json
from UDPServer import UDPServer
import BuildAndDownloand
from ProjectDBAccess import DBAccesser

class CMDProcesser:
    udp_server = None

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
        self.udp_server = UDPServer(host, port)
    

    def __del__(self):
        if self.udp_server:
            del self.udp_server
    

    def  request_analysis(self, request_data):
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
                    args["task_id"] = int(param_list[2])
                    cmd = param_list[0]
                except:
                    cmd = None
                    args = None
        elif (param_list[0] == "update_tc_info"):
            # Command format: update_tc_info -p <project_path>
            # Description: Analysis the project folder and update the project info to Database
            if (("-p" not in param_list) or
                (param_list.index("-p") != 1) or
                (len(param_list) != 3)):
                cmd = None
                args = None
            elif not os.path.exists(param_list[2]):
                cmd = None
                args = None
            else:
                cmd = param_list[0]
                args["project_path"] = param_list[2]
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
                if len(param_list) == 5:
                    if param_list[3] != "-c":
                        cmd = None
                        args = None
                    else:
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
                            args["project_id"] = int(param_list[index + 1])
                        except:
                            args = None
                            break
                    elif value == "-m":
                        args["module_id"] = param_list[index + 1]
                    elif value == "-s":
                        try:
                            args["sub_id"] = int(param_list[index + 1])
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
    

    '''
    def __alloc_process_for_cmd(self, func, args):
        process = multiprocessing.Process(target=func, args=args)
        process.start()
        return process
    '''
    

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


    def get_task_status(self, task_id):
        if len(self.task_list) == 0:
            return "None"
        # Get target task_info
        for task_info in self.task_list:
            if task_id == task_info["task_id"]:
                break
        # No target task found
        if task_info["task_id"] != task_id:
            return "None"
        # Task found but no sub-process object
        # This situation means that some issue happened in new process allocation
        if not task_info["process"]:
            return "Error"
        # The message of the task is empty
        if task_info["msg_queue"].empty():
            if not task_info["process"].is_alive():
                return "Error"
            # The sub-process is running but no new status updated
            if (time.time() - 300) > task_info["timestamp"]:
                return "Timeout"
            return "Running"
        # The message queue is not empty, it means the sub-process has updated the status to the queue
        else:
            lock = task_info["lock"]
            lock.acquire()
            try:
                data = task_info["msg_queue"].get()
            finally:
                lock.release()
            if isinstance(data, float):
                timestamp = data
                if (time.time() - 300) > timestamp:
                    return "Timeout"
                task_info["timestamp"] = timestamp
                return "Running"
            elif isinstance(data, str):
                response = data
                if response != "Done":
                    response = "Error"
                return response
            return "Error"

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
            "task_id": task_id,
            "CMD": cmd,
            "task_params": task_params,
            "process": process,
            "msg_queue": msg_queue,
            "lock": lock,
            "timestamp": time.time(),
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


    def start_service(self):
        while True:
            print("Listen CMD:")
            request_data, client_addr = self.udp_server.get_request()
            cmd, args = self.request_analysis(request_data=request_data)
            if cmd == "exit":
                print("CMD:{}".format(cmd))
                if (self.running_task_count != 0):
                    message = "Running"
                    self.udp_server.send_response(client_addr, message)
                    continue
                message = "Done"
                self.udp_server.send_response(client_addr, message)
                print("exit CMD Processer")
                break
            elif cmd == "get_task_status":
                '''
                # UDP test code
                print("CMD:{}".format(cmd))
                if args["task_id"]:
                    print("taskId:{}".format(args["task_id"]))
                message="Running"
                self.udp_server.send_response(client_addr, message)
                continue
                '''
                status = self.get_task_status(task_id=args["task_id"])
                if status == "Done" or status == "Error" or status == "Timeout":
                    self.del_task(task_id=args["task_id"])
                self.udp_server.send_response(client_addr, status)
            elif cmd == "update_tc_info":
                '''
                # UDP test code
                print("CMD:{}".format(cmd))
                if args["project_path"]:
                    print("projectPath:{}".format(args["project_path"]))
                message="Done"
                self.udp_server.send_response(client_addr, message)
                continue
                '''
                # TBD
                # Step 1: Get project information by project id, such as save path
                # Step 2: Analysis the compile and download tool path
                # Step 3: Analysis the test case code to get tc_node_name, module_id, sub_id
                db_accesser = DBAccesser()
                message = db_accesser.update_project_info(project_path=args["project_path"])
                self.udp_server.send_response(client_addr, message)
                continue
            elif cmd == "update_tc_code":
                print("CMD:{}".format(cmd))
                if args["project_id"]:
                    print("projectId:{}".format(args["project_id"]))
                response="Done"
                self.udp_server.send_response(client_addr, response)
                continue
                # TBD
                # Step 1: Get test code path by project id by accessing database
                # Setp 2: Call Git function to update test case code
                pass
            elif cmd == "build_and_download":
                '''
                # UDP test code
                print("CMD:{}".format(cmd))
                if args["project_id"]:
                    print("projectId:{}".format(args["project_id"]))
                if args["module_id"]:
                    print("moduleId:{}".format(args["module_id"]))
                if args["sub_id"]:
                    print("subId:{}".format(args["sub_id"]))
                response="Running"
                self.udp_server.send_response(client_addr, response)
                continue
                '''
                task_id = self.__start_build_and_download(project_id=args["project_id"],
                                                           module_id=args["module_id"],
                                                           sub_id=args["sub_id"])
                self.udp_server(client_addr, task_id)
                continue
            else:
                print("CMD:{}".format(cmd))
                response="Error"
                self.udp_server.send_response(client_addr, response)


if __name__ == "__main__":
    cmd_processer = CMDProcesser()
    cmd_processer.start_service()
    del cmd_processer