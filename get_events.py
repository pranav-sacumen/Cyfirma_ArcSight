from datetime import datetime
from time import sleep
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from configparser import ConfigParser
import logging
import json
import traceback
logging.basicConfig(level=logging.DEBUG, filename='decyfir.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')

try:
    conf_parser = ConfigParser()
    conf_parser.read('cyfirma_config.ini')
    api_key = conf_parser.get('creds', 'api_key')
    interval = conf_parser.get('scheduler','interval')
    api_list = conf_parser.get('sources', 'API')
    if api_list:
        api_list=[item.strip() for item in api_list.split(",")]
        logging.info(f"Found these APIs: {api_list}")
    else:
        raise Exception("No API provided")

except Exception as e:
    logging.error("Config file is not in correct format. Please check the config file.")



def fetch_store_data(name, datatype="attack-surface"):
    try:
        checkpoint = ""
        with open("./checkpoints.json", "r") as checkpoint_fp:
            checkpoints = json.load(checkpoint_fp)
            if checkpoints.get(name):
                checkpoint = checkpoints.get(name)
            else:
                checkpoint = datetime.utcnow().timestamp()
        
        url = f"https://decyfir.cyfirma.com/core/api-ua/v2/alerts/{datatype}?type={name}&key={api_key}&is-full-data-view=true"
        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()

        with open(f"./outputs/{name}.json", "a") as fp:
            json.dump(data, fp)

        with open("./checkpoints.json", "r") as checkpoint_fp:
            checkpoints = json.load(checkpoint_fp)

        checkpoints[name] = checkpoint
        with open("./checkpoints.json", "w") as checkpoint_fp:
            json.dump(checkpoints, checkpoint_fp)


    except Exception as e:
        logging.error(f"Error: {e}")
        logging.error(traceback.print_exc())


# for name in api_list:
#     fetch_store_data(name)

scheduler = BackgroundScheduler()
for item in api_list:
    logging.info(f"Adding the job for {item}.")
    scheduler.add_job(func=fetch_store_data, name=item, args=[item] ,trigger="interval", minutes=int(interval), next_run_time=datetime.now())
logging.info("Starting the scheduler.")
scheduler.start()
logging.info("Scheduler started succcesfully.")
atexit.register(lambda: scheduler.shutdown())
while True:
    sleep(1)



