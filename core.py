import re
import subprocess
import random
import datetime
import os
from logging import getLogger
from config import Config
from utils import read_json_from_file, write_json_to_file


logger = getLogger("vpn_switchboard")

STOP_RUNNING_VPN = "ssh {router} /etc/init.d/openvpn stop"
GET_AVAILABLE_VPN = "ssh {router} cat /etc/config/openvpn | grep -B 2 enabled | grep -e 'config openvpn.*'"
START_VPN = "ssh {router} /etc/init.d/openvpn start {vpn}"
RESTART_FIREWALL = "ssh {router} /etc/init.d/firewall reload"
RESTART_PBR = "ssh {router} /etc/init.d/pbr reload"

class Core:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.available_vpns = self._get_available_vpns()
        
        self._stop_vpns()
        self._start_vpn(list(self.available_vpns.keys())[0])

    def _get_available_vpns(self) -> dict:
        # This is for initial setup only
        # This will set any active vpns to inactive

        def _load_vpn_list() -> list:
            output = subprocess.run(
                GET_AVAILABLE_VPN.format(router=self.config.get_router()),
                capture_output=True,
                text=True,
                shell=True
            ).stdout
            output = output.split("\n")
            vpn_list = []
            for line in output:
                match = re.match(r".*'(.*)'", line)
                if match:
                    vpn_list.append(match.group(1))
            return vpn_list

        logger.debug("Getting available VPNs")

        data = None

        if not os.path.exists("./available_vpns.json"):
            logger.debug("No available VPNs file found, creating one")
            vpn_list = _load_vpn_list()
            data = {}
            for vpn in vpn_list:
                data[vpn] = {
                    "last_download_speed": None,
                    "last_usage_time": None,
                    "download_speeds": [],
                    "average_download_speed": None,
                    "currently_active": False
                }
            write_json_to_file("./available_vpns.json", data)
        else:
            logger.debug("Available VPNs file found, loading it")
            data = read_json_from_file("./available_vpns.json")
            existing_vpns = list(data.keys())
            vpn_list = _load_vpn_list()
            for vpn in vpn_list:
                if vpn not in existing_vpns:
                    data[vpn] = {
                        "last_download_speed": None,
                        "last_usage_time": None,
                        "download_speeds": [],
                        "average_download_speed": None,
                        "currently_active": False
                    }
            for vpn in list(data.keys()):
                if data[vpn]["currently_active"]:
                    data[vpn]["currently_active"] = False
            write_json_to_file("./available_vpns.json", data)
            
        return data
    
    def _stop_vpns(self) -> None:
        logger.debug("Stopping all VPNs")
        subprocess.run(
            STOP_RUNNING_VPN.format(router=self.config.get_router()),
            shell=True
        )

        for vpn in self.available_vpns:
            self.available_vpns[vpn]["currently_active"] = False
        

    def _start_vpn(self, vpn: str) -> None:
        logger.info(f"Starting VPN: {vpn}")
        subprocess.run(
            START_VPN.format(router=self.config.get_router(), vpn=vpn),
            shell=True,
            capture_output=True,
            text=True
        )
    

    def start_next_vpn(self) -> None:
        logger.debug("Will connect to a new best VPN")
        vpn = self._get_best_vpn()
        
        self._stop_vpns()

        self.available_vpns[vpn]["currently_active"] = True
        self.available_vpns[vpn]["last_usage_time"] = datetime.datetime.now()
        self.available_vpns[vpn]["last_download_speed"] = None
        self.available_vpns[vpn]["download_speeds"] = []
        self.available_vpns[vpn]["average_download_speed"] = None
        
        self._start_vpn(vpn)
        write_json_to_file("./available_vpns.json", self.available_vpns)

    def _get_best_vpn(self) -> str:
        # If there any vpns that arent active and last_usage_time is None, randomly pick one of them 
        # since we need to gather data on all available vpns

        logger.debug("Choosing best VPN")

        unused_vpns = [vpn for vpn in self.available_vpns if not self.available_vpns[vpn]["currently_active"] and self.available_vpns[vpn]["last_usage_time"] is None]

        if len(unused_vpns) > 0:
            return random.choice(unused_vpns)
        
        # If there are no unused vpns, pick the one with the highest average download speed
        return max(self.available_vpns, key=lambda x: self.available_vpns[x]["average_download_speed"])
    
    def test_internet_connectivity(self) -> bool:
        logger.debug("Testing internet connectivity")
        # Test internet connectivity by pinging a reliable server
        try:
            # Ping Google's DNS server
            result = subprocess.run(
                ['ping', '-c', '4', '8.8.8.8'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False
        
    def set_active_current_download_speed(self, download_speed: float) -> None:
        logger.debug("Updating active VPN download speed")
        for vpn in self.available_vpns:
            if self.available_vpns[vpn]["currently_active"]:
                self.available_vpns[vpn]["last_download_speed"] = download_speed
                self.available_vpns[vpn]["download_speeds"].append(download_speed)
                self.available_vpns[vpn]["average_download_speed"] = round(sum(self.available_vpns[vpn]["download_speeds"]) / len(self.available_vpns[vpn]["download_speeds"]), 2)
        write_json_to_file("./available_vpns.json", self.available_vpns)

    def restart_firewall_and_pbr(self) -> None:
        logger.debug("Restarting firewall and PBR")
        subprocess.run(
            RESTART_FIREWALL.format(router=self.config.get_router()),
            shell=True
        )
        
        subprocess.run(
            RESTART_PBR.format(router=self.config.get_router()),
            shell=True
        )