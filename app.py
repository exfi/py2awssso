from os import getenv
from os import path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep
from pickle import load as pkl_load
from pickle import dump as pkl_save
from clipboard import paste
from vault.bitwarden import BitWarden
from vault.py2mfa import Py2Vault
from configparser import ConfigParser as cfgParser
from pprint import pprint


# Base
_PATH = path.dirname(path.abspath(__file__))
DIV = ('-' * 60)

# Config
cfg = cfgParser()
cfg.read(f'{_PATH}/config.ini')

# Selenium
WEBDRIVER_NAME = 'driver/chromedriver'
WEBDRIVER_OPT = '--window-size=800,600'

# AWS
SSO_URL = getenv('AWS_SSO_URL', '') or cfg.get('aws', 'sso_url')
APPS_ID = getenv('AWS_SSO_APPSID', '') or cfg.get('aws', 'apps_id')
ACCOUNT_NAME = getenv('AWS_PROFILE', 'default')
ACCOUNT_ID = getenv('AWS_ACCOUNT_ID', '0000')
CREDS_FILE = f"{getenv('HOME', '~')}/.aws/credentials" or cfg.get('aws', 'creds_file')

# Vault
# VAULT_OID = cfg.get('vault', 'oid')
# vault = BitWarden(VAULT_OID)
vault = Py2Vault


class SSO:
    def __init__(self):
        print(DIV)
        print('Init WebDriver ...')
        options = Options()
        options.headless = False
        options.add_argument(WEBDRIVER_OPT)
        self.driver = webdriver.Chrome(
            options=options, executable_path=f'{_PATH}/{WEBDRIVER_NAME}')
        self.driver.get(SSO_URL)

    def login_user(self):
        print(DIV)
        print('Login User ...')
        input_username = self.driver.find_element_by_id('wdc_username')
        input_username.send_keys(vault.get('username'))

        input_password = self.driver.find_element_by_id('wdc_password')
        input_password.send_keys(vault.get('password'))

        input_button = self.driver.find_element_by_id('wdc_login_button')
        input_button.click()

        sleep(4)
        if self.driver.find_elements_by_xpath('//*[@routerlink="/signout"]'):
            return True
        elif self.driver.find_element_by_id('wdc_mfacode'):
            return 'wfa'
        else:
            return False

    def login_mfa(self):
        print(DIV)
        print('Login MFA ...')
        input_mfa = self.driver.find_element_by_id('wdc_mfacode')
        input_mfa.send_keys(vault.get('totp'))

        input_button = self.driver.find_element_by_id('wdc_login_button')
        input_button.click()

        sleep(4)
        if self.driver.find_elements_by_xpath('//*[@routerlink="/signout"]'):
            return True
        else:
            return False

    def login(self):
        first = self.login_user()
        if 'wfa' in first:
            wfa = self.login_mfa()
            if wfa:
                return True
        elif first:
            return True
        else:
            print('Failed login')

    def apps(self):
        print(DIV)
        print('Open Apps AWS ...')
        input_apps = self.driver.find_element_by_id(APPS_ID)
        input_apps.click()

    def account(self):
        print(DIV)
        print(f'Find the account {ACCOUNT_NAME}/({ACCOUNT_ID}) ...')
        sleep(3)
        input_account = self.driver.find_elements_by_xpath(
            f'//*[contains(text(), "{ACCOUNT_ID}") and @class="accountId"]')
        if input_account:
            input_account[0].click()
            return True
        else:
            print(
                f'Not exist the account {ACCOUNT_NAME} ...')
            return False

    def credentials(self):
        print(DIV)
        print('Get Credentials from Role ??? ...')
        sleep(3)
        profile = self.driver.find_elements_by_xpath(
            '//*[@class="desktop-profile"]')
        profile[0].find_element_by_class_name('creds-link').click()
        sleep(3)

        input_access_key_id = self.driver.find_elements_by_xpath(
            '//*[@id="copy-accessKeyId"]')
        input_access_key_id[0].find_element_by_class_name('copy-value').click()
        sleep(3)
        access_key_id = paste()
        # print(f'access_key_id = {access_key_id}')

        input_secret_access_key = self.driver.find_elements_by_xpath(
            '//*[@id="copy-secretAccessKey"]')
        input_secret_access_key[0].find_element_by_class_name(
            'copy-value').click()
        sleep(3)
        secret_access_key = paste()
        # print(f'secret_access_key = {secret_access_key}')

        input_session_token = self.driver.find_elements_by_xpath(
            '//*[@id="copy-sessionToken"]')
        input_session_token[0].find_element_by_class_name('copy-value').click()
        sleep(3)
        session_token = paste()
        # print(f'session_token = {session_token}')

        creds = {
            'access_key_id': access_key_id,
            'secret_access_key': secret_access_key,
            'session_token': session_token
        }

        self.credentials_save(creds)

    def credentials_save(self, cred):
        print(DIV)
        print('Save Credentials in .aws/credentials ...')
        # pprint(cred)
        aws_cfg = cfgParser()
        aws_cfg.read(CREDS_FILE)
        aws_cfg.set(ACCOUNT_NAME, 'aws_access_key_id', cred['access_key_id'])
        aws_cfg.set(ACCOUNT_NAME, 'aws_secret_access_key',
                    cred['secret_access_key'])
        aws_cfg.set(ACCOUNT_NAME, 'aws_session_token', cred['session_token'])

        with open(CREDS_FILE, 'w') as f:
            aws_cfg.write(f)

    def main(self):
        sleep(5)
        try:
            if 'aval-aws' in self.driver.title:
                login = self.login()
                if login:
                    self.apps()
                    account = self.account()
                    if account:
                        self.credentials()
                        self.driver.quit()
                    else:
                        self.driver.quit()
                else:
                    self.driver.quit()
            else:
                self.driver.quit()
        except Exception:
            print(Exception)
            self.driver.quit()


if __name__ == "__main__":
    print(DIV)
    print('Start app ...')
    SSO().main()
    print(DIV)
    print('Finish app ...')
    print(DIV)
