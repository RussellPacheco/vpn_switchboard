from configparser import ConfigParser
import os
from logging import getLogger

logger = getLogger("vpn_switchboard")



class Config:
    def __init__(self, config_file: str) -> None:
        self.config = ConfigParser()

        if not os.path.exists(config_file):
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            self._create_config(config_file)

        self.config.read(config_file)
        

    def _create_config(self, config_file: str) -> None:
        self.config["GENERAL"] = {}

        self.config["GENERAL"]["download_threshold"] = '15'
        self.config["GENERAL"]["router"] = "192.168.1.1"
        with open(config_file, "w") as f:
            logger.debug("Creating configuration file: %s", config_file)
            self.config.write(f)

    def get_config(self) -> ConfigParser:
        return self.config
    
    def get_download_threshold(self) -> int:
        return int(self.config["GENERAL"]["download_threshold"])
    
    def get_router(self) -> str:
        return self.config["GENERAL"]["router"]
    
    