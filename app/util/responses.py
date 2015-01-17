import json

from flask import Response

class APIResponse(Response):
    def __init__(self, obj={}):
        Response.__init__(self)

        if not 'success' in obj:
            obj['success'] = True

        self.data = json.dumps(obj)
        self.mimetype = "application/json"

