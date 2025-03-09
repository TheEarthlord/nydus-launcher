
class StatusMsg:

    def __init__(self, idnum, msg):
        assert isinstance(idnum, int) and idnum > 0, "Status message id number must be a positive integer; was {}".format(idnum)
        assert isinstance(msg, str) and len(msg) > 0, "Status message must be a string; was {}".format(msg)
        self.idnum = idnum
        self.msg = msg

    def get_id(self):
        return self.idnum

    def get_msg(self):
        return self.msg
