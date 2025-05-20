import os
import time
import threading
from flask import Flask, render_template_string, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, \
    StaleElementReferenceException

app = Flask(__name__)


HF_EMAIL = "your-mail/username"
HF_PASSWORD = "your password"


DOWNLOAD_DIR = os.path.join(os.getcwd(), "huggingface_downloads")
ERROR_SCREENSHOT_PATH_BASE = os.path.join(os.getcwd())

if not HF_EMAIL or not HF_PASSWORD:
    print("ERROR: HF_EMAIL or HF_PASSWORD is not set. Please configure them.")


def get_screenshot_path(filename_prefix="error"):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return os.path.join(ERROR_SCREENSHOT_PATH_BASE, f"{filename_prefix}_{timestamp}.png")


def run_huggingface_automation():
    print("Starting Hugging Face automation...")
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Created download directory: {DOWNLOAD_DIR}")

    chrome_options = Options()
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--start-maximized")

    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        print("WebDriver initialized.")
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return

    wait = WebDriverWait(driver, 25)
    short_wait = WebDriverWait(driver, 15)
    very_short_wait = WebDriverWait(driver, 5)

    try:
        # 1. Go to login page
        print("Navigating to Hugging Face login page...")
        driver.get("https://huggingface.co/login")

        # Accept cookies if present
        try:
            print("Looking for cookie consent button...")
            cookie_button_xpaths = [
                "//button[contains(., 'Accept all')]",
                "//button[contains(., 'Manage cookies')]/following-sibling::button[contains(., 'Accept')]",
                "//div[contains(@class, 'cookie-banner')]//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]"
            ]
            cookie_button = None
            for xpath in cookie_button_xpaths:
                try:
                    cookie_button = short_wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    if cookie_button: break
                except TimeoutException:
                    continue
            if cookie_button:
                cookie_button.click()
                print("Accepted cookies.")
                time.sleep(1)
            else:
                print("Cookie consent button not found, proceeding...")
        except Exception as e_cookie:
            print(f"Error handling cookie button: {e_cookie}, proceeding...")

        # 2. Enter credentials
        print("Entering credentials...")
        if not HF_EMAIL or not HF_PASSWORD:
            raise ValueError("Credentials are not available (HF_EMAIL or HF_PASSWORD).")

        print("Waiting for username/email field (name='username')...")
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        email_field.send_keys(HF_EMAIL)

        print("Waiting for password field (name='password')...")
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(HF_PASSWORD)

        print("Locating login button...")
        login_button_xpaths_to_try = [
            "//form//button[@type='submit' and normalize-space(.)='Login']",
            "//button[normalize-space(.)='Login']",
            "//form//button[@type='submit']"
        ]
        login_button = None
        selected_xpath_login = ""
        for xpath in login_button_xpaths_to_try:
            try:
                print(f"Attempting to find login button with XPath: {xpath}")
                short_wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                login_button = short_wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if login_button:
                    selected_xpath_login = xpath
                    print(f"Login button found and clickable with XPath: {selected_xpath_login}")
                    break
            except TimeoutException:
                print(f"Login button not found/clickable with XPath: {xpath}")
                continue

        if not login_button:
            spath = get_screenshot_path("login_button_not_found")
            driver.save_screenshot(spath)
            raise Exception(f"Could not find login button. Screenshot: {spath}")

        print(f"Login button ID'd. Attempting click sequence...")
        try:
            print("Attempt 1: Standard Selenium click.")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", login_button)
            time.sleep(0.5)
            login_button.click()
            print("Login submitted using standard click.")
        except (ElementClickInterceptedException, StaleElementReferenceException) as e_std_click_specific:
            print(f"Standard click failed ({type(e_std_click_specific).__name__}). Trying JS click...")
            try:
                print("Attempt 2: JavaScript click.")
                driver.execute_script("arguments[0].click();", login_button)
                print("Login submitted using JavaScript click.")
            except Exception as e_js_click:
                spath = get_screenshot_path("login_button_js_click_failed")
                driver.save_screenshot(spath)
                raise Exception(f"JS click also failed for login. Screenshot: {spath}")
        except Exception as e_click_general:
            spath = get_screenshot_path("login_button_std_click_failed")
            driver.save_screenshot(spath)
            raise Exception(f"Std click failed for login unexpectedly. Screenshot: {spath}")

        # 3. Wait for successful login indicators
        print("Waiting for successful login indicators...")
        login_confirmed = False
        avatar_xpath_primary = "//header//nav[@aria-label='Main']//img[contains(@class, 'rounded-full') and contains(@src, '/avatars/')]"
        avatar_xpath_fallback = "//header//button[.//img[contains(@src, '/avatars/')]]"
        logout_form_xpath = "//form[@action='/logout']"
        expected_dashboard_url = "https://huggingface.co/"

        try:
            print("Checking for avatar image (primary selector)...")
            WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, avatar_xpath_primary)))
            print("Avatar image (primary) found and visible.")
            login_confirmed = True
        except TimeoutException:
            print("Avatar image (primary) not found or not visible.")
            try:
                print("Checking for avatar image (fallback selector)...")
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, avatar_xpath_fallback)))
                print("Avatar image (fallback) found and visible.")
                login_confirmed = True
            except TimeoutException:
                print("Avatar image (fallback) not found or not visible.")

        if not login_confirmed:
            try:
                print("Checking for logout form...")
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, logout_form_xpath)))
                print("Logout form found.")
                login_confirmed = True
            except TimeoutException:
                print("Logout form not found.")

        if not login_confirmed:
            print("Checking if URL changed from login page and matches dashboard...")
            try:
                WebDriverWait(driver, 10).until(EC.not_(EC.url_contains("/login")))
                current_url_after_login = driver.current_url
                if current_url_after_login.rstrip('/') == expected_dashboard_url.rstrip('/'):
                    print(f"URL is now {current_url_after_login} (expected dashboard) and not /login.")
                    login_confirmed = True
                else:
                    print(
                        f"URL changed from /login to {current_url_after_login}, but not to expected {expected_dashboard_url}.")
            except TimeoutException:
                print("URL did not change from /login in time.")

        if not login_confirmed:
            spath = get_screenshot_path("login_confirmation_failed_multi_check")
            driver.save_screenshot(spath)
            print(
                f"Login submitted, but confirmation indicators (avatar, logout form, URL change) not found. Screenshot: {spath}")
            raise Exception("Login confirmation failed using multi-indicator check.")

        print("Successfully logged in indication received. On home/dashboard page.")
        time.sleep(3)

        # 4. Go to Spaces page
        print("Navigating to Spaces page...")
        spaces_link_xpath_option1 = "//nav[@aria-label='Main']//a[@href='/spaces' and normalize-space(substring-after(.,'</svg>'))='Spaces']"
        spaces_link_xpath_option2 = "//nav[@aria-label='Main']//a[@href='/spaces'][contains(., 'Spaces')]"
        spaces_link_xpath_option3 = "//a[@href='/spaces' and (normalize-space(.)='Spaces' or .//span[normalize-space()='Spaces'])]"
        spaces_link_xpath_option4 = "//a[@href='/spaces']"

        spaces_link_xpaths_to_try = [
            spaces_link_xpath_option1,
            spaces_link_xpath_option2,
            spaces_link_xpath_option3,
            spaces_link_xpath_option4,
        ]
        spaces_link = None
        selected_xpath_spaces = ""
        for xpath_idx, xpath_spaces in enumerate(spaces_link_xpaths_to_try):
            try:
                print(f"Attempting to find Spaces link with XPath ({xpath_idx + 1}): {xpath_spaces}")
                spaces_link_candidate = wait.until(EC.visibility_of_element_located((By.XPATH, xpath_spaces)))
                if spaces_link_candidate.is_enabled():
                    spaces_link = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_spaces)))
                    if spaces_link:
                        selected_xpath_spaces = xpath_spaces
                        print(f"Spaces link found and clickable with XPath: {selected_xpath_spaces}")
                        break
                else:
                    print(f"Spaces link found with {xpath_spaces} but was not enabled.")
            except TimeoutException:
                print(f"Spaces link not found/visible/clickable with XPath: {xpath_spaces}")
                continue

        if not spaces_link:
            spath = get_screenshot_path("spaces_link_not_found")
            driver.save_screenshot(spath)
            raise Exception(f"Could not find Spaces link. Screenshot: {spath}")

        print(f"Spaces link ID'd. Clicking with XPath: {selected_xpath_spaces}...")
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", spaces_link)
            time.sleep(0.5)
            spaces_link.click()
        except Exception as e_space_click:
            print(f"Standard click for Spaces link failed: {e_space_click}. Trying JS click.")
            driver.execute_script("arguments[0].click();", spaces_link)

        print("Waiting for Spaces page URL to load...")
        wait.until(EC.url_contains("/spaces"))
        print("Successfully navigated to Spaces page.")
        time.sleep(3)

        # 5. Search for "Gemini Chatbot"
        print("Searching for 'Gemini Chatbot'...")
        search_input_selectors = [
            (By.XPATH, "//input[@placeholder='Filter by user, name or task']"),
            (By.XPATH, "//input[@aria-label='Filter spaces']"),
            (By.XPATH, "//input[(@type='search' or @type='text') and contains(@placeholder, 'Filter')]")
        ]
        search_input = None
        for by, value in search_input_selectors:
            try:
                search_input = short_wait.until(EC.visibility_of_element_located((by, value)))
                if search_input and search_input.is_enabled():
                    print(f"Search input found with: {by} {value}")
                    break
                else:
                    search_input = None
            except TimeoutException:
                continue

        if not search_input:
            spath = get_screenshot_path("search_input_not_found")
            driver.save_screenshot(spath)
            raise Exception(f"Could not find search input on Spaces page. Screenshot: {spath}")

        search_input.clear()
        search_input.send_keys("Gemini Chatbot")
        search_input.send_keys(Keys.RETURN)
        print("Search submitted.")
        time.sleep(4)

        # 6. Open the specific result "Chatbot using gemini"
        print("Looking for specific Space: '/spaces/moazzamdev/Chatbot-using-gemini'")

        target_space_href = "/spaces/moazzamdev/Chatbot-using-gemini"
        target_space_title_text = "Chatbot Using Gemini"

        specific_space_xpath_href = f"//a[@href='{target_space_href}']"
        specific_space_xpath_title_complex = f"//article[.//h4[normalize-space()='{target_space_title_text}']]//a[contains(@href, '/spaces/') and .//h4[normalize-space()='{target_space_title_text}']]"
        specific_space_xpath_title_simple = f"//a[.//h4[normalize-space()='{target_space_title_text}'] and contains(@href,'/spaces/')]"
        general_target_xpath = f"//article[.//h4[normalize-space(.)='{target_space_title_text}']]//a[1]"

        target_space_xpaths_to_try = [
            specific_space_xpath_href,
            specific_space_xpath_title_simple,
            specific_space_xpath_title_complex,
            general_target_xpath
        ]

        target_space_link = None
        selected_target_xpath = ""

        for xpath_idx, xpath in enumerate(target_space_xpaths_to_try):
            try:
                print(f"Attempting to find target space with XPath ({xpath_idx + 1}): {xpath}")
                candidate_elements = short_wait.until(EC.visibility_of_all_elements_located((By.XPATH, xpath)))
                if not candidate_elements:
                    print(f"No elements visible for XPath: {xpath}")
                    continue
                for candidate_link_element in candidate_elements:
                    if candidate_link_element.get_attribute('href') == target_space_href:
                        print(f"Exact href match found with XPath: {xpath}")
                        target_space_link = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable(candidate_link_element))
                        if target_space_link:
                            selected_target_xpath = xpath
                            break
                    if not target_space_link and candidate_link_element.is_displayed() and candidate_link_element.is_enabled():
                        temp_link = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(candidate_link_element))
                        if temp_link:
                            target_space_link = temp_link
                            selected_target_xpath = xpath
                            print(
                                f"Target Space link found (general) and clickable with XPath: {selected_target_xpath}")
                            break
                if target_space_link:
                    break
            except TimeoutException:
                print(f"Target Space link not found or not clickable with XPath: {xpath}")
                continue

        if not target_space_link:
            spath = get_screenshot_path("target_space_not_found")
            driver.save_screenshot(spath)
            raise Exception(f"Could not find the target Space '{target_space_title_text}'. Screenshot: {spath}")

        space_url_actual = target_space_link.get_attribute('href')
        print(f"Target Space link found: {space_url_actual}. Clicking...")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", target_space_link)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", target_space_link)

        print(f"Waiting for navigation to the Space page: {space_url_actual}")
        try:
            unique_part_of_url = space_url_actual.split('/')[-1]
            if not unique_part_of_url and len(space_url_actual.split('/')) > 1:
                unique_part_of_url = space_url_actual.split('/')[-2]

            if unique_part_of_url:
                print(f"Waiting for URL to contain: '{unique_part_of_url}'")
                wait.until(EC.url_contains(unique_part_of_url))
            else:
                print(f"Waiting for URL to match exactly (fallback): {space_url_actual}")
                wait.until(EC.url_to_be(space_url_actual))
        except Exception as e_url_wait:
            print(f"Error waiting for URL: {e_url_wait}. Current: {driver.current_url}")
            time.sleep(2)
            current_url_check = driver.current_url
            if not (
                    unique_part_of_url and unique_part_of_url in current_url_check) and current_url_check != space_url_actual:
                spath = get_screenshot_path("space_navigation_failed")
                driver.save_screenshot(spath)
                raise Exception(
                    f"Failed to navigate to target space. Current URL: {current_url_check}. Screenshot: {spath}")

        print("Successfully navigated to the target Space page.")
        time.sleep(3)

        # 7. Go to Files tab
        print("Navigating to Files tab...")
        files_tab_xpath_option1 = "//a[contains(@href, '/tree/main') and (normalize-space(.)='Files' or .//span[normalize-space(.)='Files'])]"
        files_tab_xpath_option2 = "//a[contains(@href, '/tree/main')]"
        files_tab_xpath_option3 = "//a[contains(@class, 'tab-alternate') and (normalize-space(.)='Files' or .//span[normalize-space(.)='Files'])]"

        files_tab_xpaths_to_try = [
            files_tab_xpath_option1,
            files_tab_xpath_option2,
            files_tab_xpath_option3,
        ]

        files_tab_link = None
        selected_files_tab_xpath = ""

        for xpath_idx, xpath in enumerate(files_tab_xpaths_to_try):
            try:
                print(f"Attempting to find Files tab with XPath ({xpath_idx + 1}): {xpath}")
                element_present = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                element_visible = wait.until(EC.visibility_of(element_present))

                if element_visible.is_enabled():
                    files_tab_link = wait.until(EC.element_to_be_clickable(element_visible))
                    if files_tab_link:
                        selected_files_tab_xpath = xpath
                        print(f"Files tab found and clickable with XPath: {selected_files_tab_xpath}")
                        break
                else:
                    print(f"Files tab found with {xpath} but was not enabled.")
            except TimeoutException:
                print(f"Files tab not found or not interactable with XPath: {xpath}")
                continue

        if not files_tab_link:
            spath = get_screenshot_path("files_tab_not_found")
            driver.save_screenshot(spath)
            print(f"Current URL when Files tab not found: {driver.current_url}")
            raise Exception(f"Could not find the Files tab after trying multiple XPaths. Screenshot: {spath}")

        print(f"Files tab identified. Clicking with XPath: {selected_files_tab_xpath}...")
        try:
            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", files_tab_link)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", files_tab_link)
            print("Clicked Files tab using JavaScript.")
        except Exception as e_click_files_tab:
            print(f"Error clicking Files tab: {e_click_files_tab}")
            spath = get_screenshot_path("files_tab_click_error")
            driver.save_screenshot(spath)
            raise Exception(f"Failed to click the Files tab. Screenshot: {spath}")

        print("Waiting for Files page URL to load (containing '/tree/main' or '/files')...")
        WebDriverWait(driver, 20).until(
            EC.any_of(
                EC.url_contains("/tree/main"),
                EC.url_contains("/files")
            )
        )
        current_files_url = driver.current_url
        print(f"Successfully on Files tab/page. Current URL: {current_files_url}")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//table | //div[contains(@class, 'file-explorer')] | //div[contains(text(), 'MB')] | //div[contains(text(), 'kB')] | //*[@id='repo-files-table']"))
                # Added common table ID
            )
            print("File listing area seems to be present.")
        except TimeoutException:
            print("Warning: File listing area indicator not found quickly, but proceeding.")

        time.sleep(4)

        # 8. Download all files
        print("Attempting to download files...")
        download_link_xpaths = [
            "//a[@title='Download file' and (contains(@href, '/resolve/main/') or contains(@href, '/raw/main/'))]",
            "//a[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')] and (contains(@href, '/resolve/main/') or contains(@href, '/raw/main/'))]",
            "//table[@id='repo-files-table']//tbody//tr//a[contains(@href, '/resolve/main/') or contains(@href, '/raw/main/')][not(contains(., '..'))]",
            # More specific to the files table
            "//a[contains(@href, 'download=true')]"
        ]

        file_download_links_elements = []
        for xpath in download_link_xpaths:
            try:
                links = very_short_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
                if links:
                    print(f"Found {len(links)} potential links with {xpath}")
                    file_download_links_elements.extend(links)
            except TimeoutException:
                print(f"No links found with {xpath}")
            except Exception as e_find:
                print(f"Error finding links with {xpath}: {e_find}")

        unique_file_download_links = []
        seen_hrefs = set()
        for link_el in file_download_links_elements:
            try:
                href = link_el.get_attribute("href")
                # Ensure it's a legitimate download link structure and not a folder link
                if href and href not in seen_hrefs and \
                        ("resolve/main" in href or "raw/main" in href or "download=true" in href) and \
                        not href.endswith("/"):  # Simple check to exclude folder links

                    if link_el.is_displayed() and link_el.is_enabled():
                        unique_file_download_links.append(link_el)
                        seen_hrefs.add(href)
                    else:
                        print(f"Skipping non-interactable link: {href}")
            except StaleElementReferenceException:
                print(f"Stale element encountered while processing download links.")
                continue

        if unique_file_download_links:
            print(f"Found {len(unique_file_download_links)} unique, interactable file(s) to download.")
            for i, link_element in enumerate(unique_file_download_links):
                file_name = "unknown_file"
                try:
                    file_url = link_element.get_attribute("href")
                    file_name = file_url.split("/")[-1].split("?")[0] if file_url else f"link_{i + 1}"
                    print(
                        f"Attempting to download file {i + 1}/{len(unique_file_download_links)}: {file_name} from {file_url}")

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                                          link_element)
                    time.sleep(0.75)

                    clickable_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(link_element))
                    # Forcing download if simple click doesn't work due to JS or other handlers
                    if "download=true" not in file_url:
                        if "?" in file_url:
                            download_url = file_url + "&download=true"
                        else:
                            download_url = file_url + "?download=true"
                        print(f"Attempting direct download via modified URL: {download_url}")
                        driver.get(download_url)  # This will navigate and trigger download
                        time.sleep(2)  # Give browser time to process direct GET download
                    else:
                        clickable_link.click()  # Standard click if download=true is already there

                    print(f"Download initiated for {file_name}. Check download directory: {DOWNLOAD_DIR}")
                    time.sleep(5)  # Increased wait for download to start/browser to handle
                except Exception as e_download:
                    print(f"Could not download file '{file_name}': {type(e_download).__name__} - {e_download}")
                    # Fallback to JS click on original element if direct GET failed or wasn't applicable
                    try:
                        print(f"Trying JavaScript click on original element for {file_name} as fallback...")
                        driver.execute_script("arguments[0].click();", link_element)
                        print(f"JS Clicked download for {file_name}. Check {DOWNLOAD_DIR}")
                        time.sleep(5)
                    except Exception as e_js_click:
                        print(f"JS click also failed for {file_name}: {type(e_js_click).__name__} - {e_js_click}")
        else:
            spath = get_screenshot_path("no_files_to_download")
            driver.save_screenshot(spath)
            print(f"No files found to download on the Files tab. Screenshot: {spath}")

        print(f"Automation script finished. Downloads (if any) should be in {DOWNLOAD_DIR}.")
        time.sleep(15)

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
        if driver:
            spath = get_screenshot_path("config_error")
            driver.save_screenshot(spath)
            print(f"Screenshot: {spath}")
    except TimeoutException as te:
        msg = te.msg if hasattr(te, 'msg') else str(te)
        print(f"A timeout occurred: {msg}")
        if driver:
            current_url = driver.current_url
            print(f"Timeout occurred on page: {current_url}")
            spath = get_screenshot_path("timeout_error")
            driver.save_screenshot(spath)
            print(f"Screenshot: {spath}")
    except Exception as e:
        print(f"An unexpected error occurred: {type(e).__name__} - {e}")
        if driver:
            current_url = driver.current_url
            print(f"Error occurred on page: {current_url}")
            spath = get_screenshot_path("unexpected_error")
            driver.save_screenshot(spath)
            print(f"Screenshot: {spath}")
    finally:
        print("Closing WebDriver.")
        if driver:
            driver.quit()
        print("Automation process complete.")


@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hugging Face Automation</title>
        <style>
            body { font-family: sans-serif; margin: 40px; background-color: #f4f4f4; text-align: center; }
            h1 { color: #333; }
            p { color: #555; }
            .button {
                background-color: #007bff; color: white; padding: 15px 25px;
                text-decoration: none; font-size: 18px; border-radius: 5px;
                border: none; cursor: pointer; transition: background-color 0.3s ease;
            }
            .button:hover { background-color: #0056b3; }
            .button:disabled { background-color: #cccccc; cursor: not-allowed; }
            .status { margin-top: 20px; font-style: italic; color: #777; min-height: 20px;}
        </style>
        <script>
            let automationRunning = false;
            async function startAutomation() {
                if (automationRunning) {
                    return;
                }
                automationRunning = true;
                const statusMsg = document.getElementById('statusMessage');
                const startButton = document.querySelector('.button');

                statusMsg.innerText = 'Automation initiated! A new browser window should open shortly... Check the console for progress.';
                startButton.disabled = true;

                try {
                    const response = await fetch('/start_automation');
                    const data = await response.json();
                    console.log(data.message);
                    if (response.ok) {
                        statusMsg.innerText = data.message + " Process running. This may take several minutes. Check console and browser.";
                    } else {
                        statusMsg.innerText = "Error starting automation: " + data.message;
                        automationRunning = false;
                        startButton.disabled = false;
                    }
                    setTimeout(() => {
                        if (automationRunning) {
                           statusMsg.innerText = "Automation attempt likely finished. Ready for another run if needed.";
                        }
                        automationRunning = false;
                        startButton.disabled = false;
                    }, 300000); // 5 minutes (increased for full download process)
                } catch (error) {
                    console.error('Error calling /start_automation:', error);
                    statusMsg.innerText = 'Error initiating automation (network or server issue). See browser console.';
                    automationRunning = false;
                    startButton.disabled = false;
                }
            }
        </script>
    </head>
    <body>
        <h1>Hugging Face Automation Control</h1>
        <p>Click the button below to start the automated process on Hugging Face.</p>
        <p><strong>If using environment variables for credentials, ensure HF_EMAIL and HF_PASSWORD are set.</strong></p>
        <button class="button" onclick="startAutomation()">Start Hugging Face Automation</button>
        <p id="statusMessage" class="status"></p>
        <p><em>The automation will open a new browser window. Watch that window and the Python console for progress.</em></p>
        <p><em>Screenshots on error will be saved in the same directory as the script.</em></p>
    </body>
    </html>
    """)


@app.route('/start_automation')
def start_automation_route():
    print("Flask: Received request to /start_automation")
    if not HF_EMAIL or not HF_PASSWORD:
        print("Flask: Credentials (HF_EMAIL, HF_PASSWORD) are not configured.")
        return {
            "message": "Error: HF_EMAIL and HF_PASSWORD are not configured. Automation cannot start."}, 400

    active_threads = [t for t in threading.enumerate() if t.name == "HuggingFaceAutomationThread"]
    if active_threads:
        print("Flask: Automation thread already running.")
        return {"message": "Automation process is already running. Please wait for it to complete."}, 409

    thread = threading.Thread(target=run_huggingface_automation, name="HuggingFaceAutomationThread")
    thread.daemon = True
    thread.start()
    print("Flask: Automation thread started.")
    return {"message": "Hugging Face automation process initiated."}


if __name__ == '__main__':
    print("Flask app starting...")
    if os.environ.get("HF_EMAIL") is None or os.environ.get("HF_PASSWORD") is None:
        if HF_EMAIL == "adul.moiz180@gmail.com":  # Check if it's still the hardcoded demo value
            print("INFO: Using hardcoded credentials for demo. For security, switch to environment variables.")
        else:
            print(
                "WARNING: HF_EMAIL or HF_PASSWORD environment variables are not set, and no default demo credentials are hardcoded. The script will likely fail at login.")
    else:
        print(f"INFO: Credentials will be used from environment variables (HF_EMAIL, HF_PASSWORD).")

    print(f"If automation runs, files will be downloaded to: {DOWNLOAD_DIR}")
    print(
        f"If an error occurs, screenshots will be saved in the script's directory (e.g., {ERROR_SCREENSHOT_PATH_BASE}\\error_*.png)")
    print("Open http://127.0.0.1:5000 in your web browser to start.")
    app.run(debug=True, use_reloader=False)
