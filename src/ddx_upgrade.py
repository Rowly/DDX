import requests
import logging
import time

BASE_IP = "192.168.1.22"

def logging_start():
    logging.basicConfig(filename="/var/log/ddx/result.log",
                        format="%(asctime)s:%(levelname)s:%(message)s",
                        level=logging.INFO)
    logging.info("ADDER: ==== Started Logging ====")


def logging_stop():
    logging.info("ADDER: ==== Stopped Logging ====")
    time.sleep(1)
    logging.shutdown()

def login():
    target = "api/auth/local"
    payload = {
                 "username": "admin",
                 "password": "password"
               }
    r = requests.post("http://%s/%s" %(BASE_IP, target), params=payload)
    assert(r.status_code == requests.codes.ok)
    return r.json()["token"]

def send_upgrade_post():
    token = login()
    target = "api/system/upgrade"
    headers = {
                 "Authorization": "Bearer %s" %token
              }
    files = {
               "file": ("filename", open("DDX_V0.03.3675.bin", "rb").read(), "application/octet-stream")
            }
    r = requests.post("http://%s/%s" %(BASE_IP, target), headers=headers, files=files)
    assert(r.status_code == requests.codes.no_content)

def check_upgrade_status():
    target = "api/system/upgrade"
    try:
        r = requests.get("http://%s/%s" %(BASE_IP, target))
    except Exception:
        time.sleep(5)
        login()
        r = requests.get("http://%s/%s" %(BASE_IP, target))
    assert(r.status_code == requests.codes.ok)
    return r.json()["state"]


if __name__ == "__main__":
    logging_start()
    execution = 0
    passes = 0
    fails = 0
    while True:
        try:
            execution += 1
            try:
                busy = True
                send_upgrade_post()
                while busy:
                    if check_upgrade_status() == "IDLE":
                        busy = False
                        passes += 1
                    else:
                        time.sleep(10)
                logging.info("ADDER: Execution %d Passes %d Fails %d" %(execution, passes, fails))
                logging.info("ADDER: ")
            except Exception as e:
                fails += 1
                logging.info("ADDER: Execution %d Passes %d Fails %d" %(execution, passes, fails))
                logging.info("ADDER: Exception caught %s" %e)
                logging.info("ADDER: ")
        except KeyboardInterrupt:
            logging_stop()
            break
