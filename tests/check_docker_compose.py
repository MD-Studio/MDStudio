import docker
from retrying import retry


def main():
    client = docker.from_env()
    container = get_container(client, 'mdstudio_crossbar_1')
    is_loaded = check_docker_compose(container, "DBComponent:")
    if not is_loaded:
        raise RuntimeError("crossbar container is not running!!")


def retry_if_false(r):
    return not r


@retry(retry_on_result=retry_if_false, stop_max_delay=3e5, wait_fixed=1e4)
def check_docker_compose(container, pattern):
    """Check that all the components are loaded correctly"""
    pattern = pattern.encode()  # Python 2 and 3 compatible
    print("waiting for crossbar container to start")
    return pattern in container.logs()


def get_container(client, name):
    """Get container by name"""
    xs = client.containers.list()
    cs = [c for c in xs if c.name == name]
    if cs:
        return cs[0]
    else:
        raise RuntimeError("Crossbar container is not running")


if __name__ == "__main__":
    main()
