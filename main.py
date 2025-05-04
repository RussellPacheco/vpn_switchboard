from argparse import ArgumentParser
import logging
import os
from config import Config
from utils import check_directory_permissions
from watch import start_watch

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-l", "--log-file", type=str, default="/var/log/vpn_switchboard/vpn_switchboard.log")
    parser.add_argument("--log-level", type=str, default="INFO", help="DEBUG, INFO, WARNING, ERROR, CRITICAL")
    parser.add_argument("-c", "--config-file", type=str, default="/etc/vpn_switchboard/main.conf")
    parser.add_argument("-w", "--watch-file", type=str, required=True)
    args = parser.parse_args()

    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % args.log_level)
    
    if not os.path.exists(os.path.dirname(args.log_file)):
        if not check_directory_permissions(args.log_file):
            raise PermissionError(f"Program does not have permission to create log directory at {os.path.dirname(args.log_file)}")
        os.makedirs(os.path.dirname(args.log_file))

    
    logger = logging.getLogger("vpn_switchboard")
    logger.setLevel(numeric_level)
    fh = logging.FileHandler(args.log_file)
    fh.setLevel(numeric_level)
    ch = logging.StreamHandler()
    ch.setLevel(numeric_level)
    formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info("Starting VPN Switchboard")
    logger.debug("Loading configuration file: %s", args.config_file)

    if not os.path.exists(args.config_file):
        if not check_directory_permissions(args.config_file):
            raise PermissionError(f"Program does not have permission to create config directory at {os.path.dirname(args.config_file)}")

    if not os.path.exists(args.watch_file):
        raise FileNotFoundError(f"Watch file not found: {args.watch_file}")    
    
    config = Config(args.config_file)

    start_watch(config=config, watch_file=args.watch_file)