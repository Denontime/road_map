import os
import json
from datetime import datetime

class Config:
    def __init__(self):
        self.AMAP_KEY = os.environ.get('AMAP_WEBSERVICE_KEY', '9a108c93d1590cf87f1a289648f30db3')
        self.OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

    def get_output_dir(self, route_name=None):
        if route_name:
            today = datetime.now().strftime('%Y%m%d')
            dir_name = f"{today}_{route_name}"
            return os.path.join(self.OUTPUT_DIR, dir_name)
        return self.OUTPUT_DIR

config = Config()