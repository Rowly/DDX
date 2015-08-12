import requests
import logging
import time

BASE_IP = "192.168.1.22"
EXECUTION = 0
PASSES = 0
FAILS = 0

def logging_start():
    logging.basicConfig(filename="/var/log/ddx/result.log",
                        format="%(asctime)s:%(levelname)s:%(message)s",
                        level=logging.INFO)
    logging.info("ADDER: ==== Started Logging ====")


def logging_stop():
    logging.info("ADDER: ==== Stopped Logging ====")
    time.sleep(1)
    logging.shutdown()

def login(retry=0):
    target = "api/auth/local"
    payload = {
                 "username": "admin",
                 "password": "password"
              }
    try:
        r = requests.post("http://%s/%s" %(BASE_IP, target), params=payload)
        assert(r.status_code == requests.codes.ok)
        return r.json()["token"]
    except requests.exceptions.ConnectionError:
        if retry < 3:
            retry += 1
            time.sleep(5)
            login(retry)
        else:
            raise

def send_upgrade_post(filename):
    token = login()
    target = "api/system/upgrade"
    headers = {
                 "Authorization": "Bearer %s" %token
              }
    files = {
               "file": ("filename", open(filename, "rb").read(), "application/octet-stream")
            }
    r = requests.post("http://%s/%s" %(BASE_IP, target), headers=headers, files=files)
    assert(r.status_code == requests.codes.no_content)

def check_upgrade_status():
    target = "api/system/upgrade"
    try:
        r = requests.get("http://%s/%s" %(BASE_IP, target))
        assert(r.status_code == requests.codes.ok)
        return r.json()
    except requests.exceptions.ConnectionError:
        time.sleep(10)
        login()
        check_upgrade_status()            

def test_for_fw(filename):
    global EXECUTION
    global PASSES
    global FAILS
    try:
        send_upgrade_post(filename)
        while True:
            response_json = check_upgrade_status()
            if response_json is None:
                response_json = check_upgrade_status()
            if (response_json["state"] == "IDLE") and (response_json["error"] == 0):
                PASSES += 1
                logging.info("ADDER: Execution %d, Passes %d, Fails %d" %(EXECUTION, PASSES, FAILS))
                break
            elif (response_json["state"] == "IN PROGRESS") and (response_json["error"] != 0):
                FAILS += 1
                logging.info("ADDER: Execution %d, Passes %d, Fails %d" %(EXECUTION, PASSES, FAILS))
                logging.info("ADDER: Error code %d State %s" %(response_json["error"], response_json["state"]))
                break
            elif (response_json["state"] == "IDLE") and (response_json["error"] != 0):
                FAILS += 1
                logging.info("ADDER: Execution %d, Passes %d, Fails %d" %(EXECUTION, PASSES, FAILS))
                logging.info("ADDER: Error code %d State %s" %(response_json["error"], response_json["state"]))
                break
            else:
                time.sleep(10)
    except Exception as e:
        FAILS += 1
        logging.info("ADDER: Execution %d, Passes %d, Fails %d" %(EXECUTION, PASSES, FAILS))
        logging.info("ADDER: %s" %e)

if __name__ == "__main__":
    logging_start()
    while True:
        try:
            EXECUTION += 1
            test_for_fw("DDX_V0.03.3675.bin")
            time.sleep(30)
            test_for_fw("DDX_V0.03.3698.bin")
            time.sleep(30)
            test_for_fw("DDX_V0.03.3698.bin")
            time.sleep(30)
        except KeyboardInterrupt:
            logging_stop()
            break
