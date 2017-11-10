from mdstudio.deferred.chainable import chainable


class TestSession:
    procedure = "test.procedure"

class APITestCase:

    @chainable
    def assertApi(self, object, method, input, auth_meta):
        registered_callable = getattr(object, method)
        result = yield registered_callable.wrapped(object, input, TestSession(), auth_meta)
        return result
