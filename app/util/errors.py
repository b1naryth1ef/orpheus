from flask import jsonify, request
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
    def __init__(self, response, mtype="danger", redirect="/"):
        self.response = response
        self.redirect = redirect
        self.mtype = mtype

    def to_response(self):
        return flashy(self.response, self.mtype, self.redirect)

class APIError(ResponseException):
    def __init__(self, msg, status_code=200):
        self.obj = {
            "message": msg,
            "success": False
        }
        self.status_code = status_code

    def to_response(self):
        resp = jsonify(self.obj)
        resp.status_code = self.status_code
        return resp

class FortException(ResponseException):
    def __init__(self, msg):
        self.msg = msg

    def to_response(self):
        if request.blueprint == 'api':
            resp = jsonify({
                "message": self.msg,
                "success": False,
            })
        else:
            resp = flashy(self.msg, "danger", "/")
        return resp

class ValidationError(FortException):
    pass

class InvalidRequestError(FortException):
    pass

class InvalidTradeUrl(FortException):
    pass

def apiassert(truthy, msg):
    if not truthy:
        raise APIError(msg)

