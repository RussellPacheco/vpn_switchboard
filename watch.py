from logging import getLogger
import re
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from config import Config
from core import Core

logger = getLogger("vpn_switchboard")

class Callback(FileSystemEventHandler):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.core = Core(config=config)
        self.config = config
        self.in_progress = False
        
    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            with open(event.src_path, "r") as f:
                content = f.read()
            if len(content) > 0:
                logger.debug("Watch file updated.")
                unprocessed = content.split("\n")
                download = unprocessed[1]
                match = re.match(r"Download:\s(.*)\sMbit/s", download)
                if match:
                    current_download_speed = float(match.group(1))
                    self.core.set_active_current_download_speed(current_download_speed)
                    threshold = self.config.get_download_threshold()
                    if current_download_speed < threshold and not self.in_progress:
                        self.in_progress = True
                        result = False
                        while not result:
                            self.core.start_next_vpn()
                            time.sleep(35)
                            result = self.core.test_internet_connectivity()
                            if not result:
                                self.core.restart_firewall_and_pbr()
                                time.sleep(35)
                                result = self.core.test_internet_connectivity()
                        self.in_progress = False

def start_watch(config: Config, watch_file: str) -> None:
    observer = Observer()
    callback = Callback(config=config)
    observer.schedule(callback, watch_file, recursive=False)
    observer.start()
    logger.info("Watching %s", watch_file)
    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()     
            
