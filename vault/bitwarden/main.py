from subprocess import check_output

class BitWarden:
    def __init__(self, oid):
        self.oid = oid

    def get(self, arg):
        result = check_output(['sh', '-c', f'bw get {arg} {self.oid}']).decode('utf-8')
        return result

# _user = _bw('username')
# _pass = _bw('password')
# _totp = _bw('totp')
