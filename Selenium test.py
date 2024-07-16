from selenium import webdriver
from selenium.webdriver.common.selenium_manager import SeleniumManager

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')  # Optional: Run Chrome in headless mode

# Initialize SeleniumManager to automatically manage the ChromeDriver
selenium_manager = SeleniumManager()
chrome_driver_path = selenium_manager.driver_path

driver = webdriver.Chrome( options=options)
driver.get("https://www.google.com")
print(driver.title)
driver.quit()