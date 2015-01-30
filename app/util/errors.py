from flask import jsonify

from util import flashy

class EmporiumException(Exception):
    pass

class ValidationError(Exception):
    pass

class InvalidRequestError(Exception):
    pass

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
    def __init__(self, msg, status_code=400):
        self.obj = {
            "message": msg,
            "success": False
        }
        self.status_code = status_code

    def to_response(self):
        resp = jsonify(self.obj)
        resp.status_code = self.status_code
        return resp

def apiassert(truthy, msg):
    if not truthy:
        raise APIError(msg)

