from Manager import DriverManager
from Utility import LoginModule
from Utility import Util
import atexit
import trex_crawler

#pip install -r requirements.txt
#pyinstaller -n "TREX Crawler ver1.0" --clean --onefile main.py

def main():
    logger = Util.Logger("Dev")
    crawler = trex_crawler.TREX_Crawler(logger)
    logger.log(log_level="Event", log_msg=f"=TREX Crawler ver1.0=")
    try:
        crawler.start_crawling()
        return
    except Exception as e:
        logger.log(log_level="Error", log_msg=e)
    finally:
        exit_program = input("Press enter key to exit the program")

main()