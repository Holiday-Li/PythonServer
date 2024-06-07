import unittest, time, BuildAndDownloand, socket, multiprocessing
from CMDProcesser import CMDProcesser
from UDPServer import UDPServer
from TCPServer import TCPServer
from TCPClient import TCPClient

'''
def loop_process(task_params, msg_que, lock):
    while True:
        time.sleep(10)
        BuildAndDownloand.update_queue_message(msg_queue=msg_que,
                                               lock=lock,
                                               message=time.time())


# Sub-process test function
# Using for get_status function
def timeout_sub_process(task_params, msg_que, lock):
    time.sleep(1)
    # Time out test
    timestamp = time.time()
    # print("\tFirst timestamp: {}".format(timestamp))
    BuildAndDownloand.update_queue_message(msg_queue=msg_que,
                                           lock=lock,
                                           message=timestamp)

    time.sleep(5)
    timestamp = time.time() - 300
    # print("\tSecond timestamp: {}".format(timestamp))
    BuildAndDownloand.update_queue_message(msg_queue=msg_que,
                                           lock=lock,
                                           message=timestamp)
    return


def done_sub_process(task_params, msg_que, lock):
    time.sleep(1)
    timestamp = time.time()

    BuildAndDownloand.update_queue_message(msg_queue=msg_que,
                                           lock=lock,
                                           message=timestamp)
    
    time.sleep(5)

    BuildAndDownloand.update_queue_message(msg_queue=msg_que,
                                           lock=lock,
                                           message="Done")
    return
'''


'''
class RequestAnalysisTest(unittest.TestCase):

    def test_invalid_cmd(self):
        cmd_processer = CMDProcesser()
        request = "invalid_cmd"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_exit_1(self):
        cmd_processer = CMDProcesser()
        request = "exit"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, "exit")
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_exit_2(self):
        cmd_processer = CMDProcesser()
        request = "exit -a"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_exit_3(self):
        cmd_processer = CMDProcesser()
        request = "exit a"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_get_test_status_1(self):
        cmd_processer = CMDProcesser()
        request = "get_task_status -t 123"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, "get_task_status")
        self.assertEqual(args["task_id"], 123)
        del cmd_processer
    
    def test_get_test_status_2(self):
        cmd_processer = CMDProcesser()
        request = "get_task_status -t abc"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_get_test_status_3(self):
        cmd_processer = CMDProcesser()
        request = "get_task_status -a 123"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_get_test_status_4(self):
        cmd_processer = CMDProcesser()
        request = "get_task_status -t 123 a"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_get_test_status_5(self):
        cmd_processer = CMDProcesser()
        request = "get_task_status 123"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_get_test_status_6(self):
        cmd_processer = CMDProcesser()
        request = "get_task_status"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_update_tc_info_1(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_info -p C:\\Users\\lichunguang\\Documents\\WorkSpace"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, "update_tc_info")
        self.assertEqual(args["project_path"], "C:\\Users\\lichunguang\\Documents\\WorkSpace")
        del cmd_processer
    
    def test_update_tc_info_2(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_info -p abc"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_update_tc_info_3(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_info -p C:\\Users\\lichunguang\\Documents\\WorkSpace abc"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_update_tc_info_4(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_info C:\\Users\\lichunguang\\Documents\\WorkSpace"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
    
    def test_update_tc_info_5(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_info"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_update_tc_code_1(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_code -p 123"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, "update_tc_code")
        self.assertEqual(args["project_id"], 123)
        del cmd_processer

    def test_update_tc_code_2(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_code -p 123 -c abc"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, "update_tc_code")
        self.assertEqual(args["project_id"], 123)
        self.assertEqual(args["commit_id"], "abc")
        del cmd_processer

    def test_update_tc_code_3(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_code -p 123 -c abc a"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_update_tc_code_4(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_code 123 -c abc"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_update_tc_code_5(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_code 123 abc"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_update_tc_code_6(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_code -p abc"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_update_tc_code_7(self):
        cmd_processer = CMDProcesser()
        request = "update_tc_code"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_1(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -p 123 -m abc1 -s 678"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, "build_and_download")
        self.assertEqual(args["project_id"], 123)
        self.assertEqual(args["module_id"], "abc1")
        self.assertEqual(args["sub_id"], 678)
        del cmd_processer

    def test_build_and_download_2(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -p abc -m abc1 -s 678"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_3(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -p 123 -m abc1 -s abc"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_4(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download 123 -m abc1 -s 456"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_5(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -p 123 abc1 -s 456"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_6(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -p 123 -m abc1 456"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_7(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -p 123 -m abc1 -s 456 a"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_8(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -p 123 -m abc1 -s 456 1"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_9(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -m abc1 -s 456"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_10(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -p 123 -s 456"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer

    def test_build_and_download_11(self):
        cmd_processer = CMDProcesser()
        request = "build_and_download -p 123 -m abc1"
        cmd, args = cmd_processer.request_analysis(request_data = request)
        self.assertEqual(cmd, None)
        self.assertEqual(args, None)
        del cmd_processer
# '''


'''
class AllocAndDelTaskTest(unittest.TestCase):
    def test_alloc_and_del_task(self):
        cmd_processer = CMDProcesser()
        task_list = []
        task_params = None
        seq = 0
        
        cmd_processer.del_task(seq)
        self.assertEqual(cmd_processer.running_task_count, 0)
        self.assertEqual(cmd_processer.task_seq, 0)

        for i in range(cmd_processer.max_task_count + 1):
            task_id = cmd_processer.alloc_process_for_task(cmd="test_{}".format(i),
                                                           task_params=task_params,
                                                           func=loop_process)
            if i < cmd_processer.max_task_count:
                self.assertEqual(task_id, seq)
                self.assertEqual(cmd_processer.running_task_count, (i + 1))
                seq += 1
                task_list.append(task_id)
            else:
                self.assertEqual(task_id, -1)
                self.assertEqual(cmd_processer.running_task_count, cmd_processer.max_task_count)
        
        self.assertEqual(cmd_processer.running_task_count, cmd_processer.max_task_count)
        cmd_processer.del_task(seq)
        self.assertEqual(cmd_processer.running_task_count, cmd_processer.max_task_count)
        self.assertEqual(cmd_processer.task_seq, seq)

        running_task_count = len(task_list)
        for task_id in task_list:
            cmd_processer.del_task(task_id)
            running_task_count -= 1
            self.assertEqual(cmd_processer.running_task_count, running_task_count)
        self.assertEqual(cmd_processer.running_task_count, 0)
        self.assertEqual(cmd_processer.task_seq, seq)
        del cmd_processer
# '''


'''
class GetStatusTest(unittest.TestCase):
    def test_invalid_task_id(self):
        cmd_processer = CMDProcesser()
        status = cmd_processer.get_task_status(task_id=cmd_processer.task_seq)
        self.assertEqual(status, "None")
        del cmd_processer

    def test_timeout_task(self):
        cmd_processer = CMDProcesser()
        task_id = cmd_processer.alloc_process_for_task(cmd="status_test",
                                                       func=timeout_sub_process,
                                                       task_params=None)
        self.assertEqual(task_id, 0)
        self.assertAlmostEqual(cmd_processer.running_task_count, 1)

        
        status = cmd_processer.get_task_status(task_id=1)
        self.assertEqual(status, "None")
        
        status = cmd_processer.get_task_status(task_id=0)
        self.assertEqual(status, "Running")

        time.sleep(2)
        status = cmd_processer.get_task_status(task_id=0)
        self.assertEqual(status, "Running")

        time.sleep(7)
        status = cmd_processer.get_task_status(task_id=0)
        self.assertEqual(status, "Timeout")
        del cmd_processer
    
    def test_done_task(self):
        cmd_processer = CMDProcesser()

        task_id = cmd_processer.alloc_process_for_task(cmd="done_test",
                                                       func=done_sub_process,
                                                       task_params=None)
        
        status = cmd_processer.get_task_status(task_id=task_id)
        self.assertEqual(status, "Running")

        time.sleep(2)
        status = cmd_processer.get_task_status(task_id=task_id)
        self.assertEqual(status, "Running")

        time.sleep(7)
        status = cmd_processer.get_task_status(task_id=task_id)
        self.assertEqual(status, "Done")
        del cmd_processer
# '''

'''
class UDPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def send_message(self, message):
        self.client.sendto(message.encode("utf-8"), (self.host, self.port))
        return

    def recv_message(self):
        return self.client.recvfrom(1024)

    def __del__(self):
        self.client.close()

def udp_server_process(host, port):
    print("Start server process")
    udp_server = UDPServer(host=host, port=port)
    print("Recv message:")
    request, client_addr = udp_server.get_request()
    print("Message:{}, ClientAddr: {}".format(request, client_addr))
    udp_server.send_response(client_addr=client_addr, data=request.upper())
    del udp_server
    return

class UDPServerTest(unittest.TestCase):
    def test_server_test(self):
        host = "127.0.0.1"
        port = 12345
        params = (host, port)
        process = multiprocessing.Process(target=udp_server_process, args=params)
        process.start()
        time.sleep(1)
        udp_client = UDPClient(host=host, port=port)
        message = "abc"
        udp_client.send_message(message)
        data, _ = udp_client.recv_message()
        self.assertEqual(data.decode("utf-8"), message.upper())
        process.join()
        del udp_client
# '''

def tcp_server_test(host, port):
    tcp_server = TCPServer(host, port)
    message, client_socket = tcp_server.get_request()
    response = message.upper()
    tcp_server.send_response(client_socket, response)
    del tcp_server
    return

class TCPServerTest(unittest.TestCase):
    def test_tcp_server(self):
        host = "127.0.0.1"
        port = 12345
        params = (host, port)
        process = multiprocessing.Process(target=tcp_server_test, args=params)
        process.start()
        time.sleep(1)
        tcp_client = TCPClient(host, port)
        message = "abc"
        tcp_client.send(message)
        response = tcp_client.recv()
        self.assertEqual(response, message.upper())
        del tcp_client



if __name__ == "__main__":
    unittest.main()