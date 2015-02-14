import json, decimal

from util import json_encoder
from flask import Response, request

class APIResponse(Response):
    def __init__(self, obj={}):
        Response.__init__(self)

        if not 'success' in obj:
            obj['success'] = True

        if request.values.get("pretty") == '1':
            self.data = json.dumps(obj,
                sort_keys=True,
                indent=2,
                separators=(',', ': '), default=json_encoder)
        else:
            self.data = json.dumps(obj, default=json_encoder)

        self.mimetype = "application/json"


