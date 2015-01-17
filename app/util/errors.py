from flask import jsonify

from util import flashy

class ResponseException(Exception):
    def to_response(self):
        raise NotImplementtedError("Must define to_response on `%s`" % self.__class__.__name__)

class GenericError(ResponseException):
    def __init__(self, msg, code=200):
        self.msg = msg
        self.code = code

    def to_response(self):
        return self.msg, self.code

class UserError(ResponseException):
    def __init__(self, response, mtype="success", redirect="/"):
        self.response = response
        self.redirect = redirect
        self.mtype = mtype

    def to_response(self):
        return flashy(self.response, self.mtype, self.redirect)

class APIError(ResponseException):
    def __init__(self, msg):
        self.obj = {
            "message": msg,
            "success": False
        }

    def to_response(self):
        return jsonify(self.obj)
