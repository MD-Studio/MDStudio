from os.path import join
from time import sleep
import json
import jsonschema
import lie_echo
import sys


if (sys.version_info > (3, 0)):
    file_exception = FileNotFoundError
else:
    file_exception = IOError


def main(path="/tmp/echo.json"):
    try:
        with open(path, "r") as f:
            d = json.load(f)
        check_echo(d)
    except file_exception:
        msg = "something went wrong calling the echo component!!"
        raise RuntimeError(msg)


def check_echo(d):
    """Check if the echo output is valid """
    root = lie_echo.__path__[0]
    path_schema = join(root, 'schemas', 'resources', 'hello-message.v1.json')
    try:
        with open(path_schema, 'r') as f:
            s = json.load(f)
        jsonschema.validate(d['message'], s)
        print("The echo component is running!!")
    except jsonschema.ValidationError:
        msg = "The echo component produced an unexpected output!!"
        raise RuntimeError(msg)


if __name__ == "__main__":
    sleep(2)  # give some time to the application to write
    main()
