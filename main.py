from Manager import DriverManager
from Utility import LoginModule
from Utility import Util
import atexit
import mra_crawler

#pip install -r requirements.txt
#pyinstaller -n "MRA Crawler ver1.5" --clean --onefile main.py

def main():
    # logger = Util.Logger("Build")
    logger = Util.Logger("Build")
    crawler = mra_crawler.MRA_Crawler(logger)
    logger.log(log_level="Event", log_msg=f"=MRA Crawler ver1.5=")
    try:
        crawler.start_crawling()
        return
    except Exception as e:
        logger.log(log_level="Error", log_msg=e)
    finally:
        exit_program = input("Press enter key to exit the program")

main()
