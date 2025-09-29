import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.bai_utils import *

if __name__=='__main__':
    ldap = sys.argv[1]
    project = sys.argv[2]
    branch = sys.argv[3]
    stage_prod = sys.argv[4]
    cluster_name = sys.argv[5]
    cluster_pass = sys.argv[6]
    fncm_version = sys.argv[7]
    
    bai = BaiUtils(ldap, project, branch, stage_prod, cluster_name, cluster_pass)
    bai.get_config_map()
    bai.get_kafka_secret()
    bai.sent_data_to_event_stream(fncm_version)