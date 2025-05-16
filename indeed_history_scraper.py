import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from msedge.selenium_tools import Edge, EdgeOptions
from dotenv import load_dotenv

class IndeedHistoryScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.setup_driver()
        
    def setup_driver(self):
        """Set up the Edge WebDriver with appropriate options."""
        edge_options = EdgeOptions()
        edge_options.use_chromium = True
        edge_options.add_argument('--start-maximized')
        edge_options.add_argument('--disable-notifications')
        
        self.driver = Edge(options=edge_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def login(self, email, password):
        """Log in to Indeed account."""
        try:
            # Navigate to Indeed sign-in page
            self.driver.get('https://secure.indeed.com/auth')
            
            # Wait for and click email login option
            email_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, 'login-google-button'))
            )
            email_button.click()
            
            # Switch to email input
            email_input = self.wait.until(
                EC.presence_of_element_located((By.ID, 'ifl-InputFormField-3'))
            )
            email_input.send_keys(email)
            
            # Click continue
            continue_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]"))
            )
            continue_button.click()
            
            # Wait for password field and enter password
            password_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, 'password'))
            )
            password_input.send_keys(password)
            
            # Click sign in
            signin_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in')]"))
            )
            signin_button.click()
            
            # Wait for successful login
            time.sleep(5)
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error during login: {str(e)}")
            return False
            
    def get_job_history(self):
        """Extract job search history."""
        try:
            # Navigate to job search history page
            self.driver.get('https://myjobs.indeed.com/applied')
            time.sleep(3)  # Wait for page to load
            
            jobs_data = []
            
            # Keep scrolling and collecting data until no more jobs are loaded
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                # Extract job information
                job_cards = self.driver.find_elements(By.CLASS_NAME, 'job-card')
                
                for card in job_cards:
                    try:
                        job_info = {
                            'title': card.find_element(By.CLASS_NAME, 'job-title').text,
                            'company': card.find_element(By.CLASS_NAME, 'company-name').text,
                            'location': card.find_element(By.CLASS_NAME, 'location').text,
                            'date_applied': card.find_element(By.CLASS_NAME, 'date-applied').text,
                            'status': card.find_element(By.CLASS_NAME, 'status').text
                        }
                        if job_info not in jobs_data:
                            jobs_data.append(job_info)
                    except NoSuchElementException:
                        continue
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Calculate new scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
            return jobs_data
            
        except Exception as e:
            print(f"Error extracting job history: {str(e)}")
            return []
            
    def save_to_csv(self, jobs_data, filename='job_history.csv'):
        """Save job history to CSV file."""
        if jobs_data:
            df = pd.DataFrame(jobs_data)
            df.to_csv(filename, index=False)
            print(f"Job history saved to {filename}")
        else:
            print("No job data to save.")
            
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()

def main():
    load_dotenv()  # Load environment variables
    
    # Get credentials from environment variables
    email = os.getenv('INDEED_EMAIL')
    password = os.getenv('INDEED_PASSWORD')
    
    if not email or not password:
        print("Please set INDEED_EMAIL and INDEED_PASSWORD environment variables")
        return
    
    scraper = IndeedHistoryScraper()
    
    try:
        if scraper.login(email, password):
            print("Successfully logged in")
            jobs_data = scraper.get_job_history()
            scraper.save_to_csv(jobs_data)
        else:
            print("Failed to log in")
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 