WORKSPACE_CACHE: dict[str, dict] = {}


def get_cached_workspace(handle: str):
    return WORKSPACE_CACHE.get(handle)


def set_cached_workspace(handle: str, workspace_data: dict):
    WORKSPACE_CACHE[handle] = workspace_data


def invalidate_cache(handle: str):
    WORKSPACE_CACHE.pop(handle, None)
