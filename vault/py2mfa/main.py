from os import getenv
import pyotp

class Py2Vault:

    @staticmethod
    def get(arg):
        if "username" in arg:
            result = getenv("AWS_SSO_USER", "")
        elif "password" in arg:
            result = getenv("AWS_SSO_PASS", "")
        elif "totp" in arg:
            totp = pyotp.TOTP(getenv("AWS_SSO_MFA", ""))
            result = totp.now()
        # print("nada")
        return result
