import os


def ensure_dir(directory: str) -> None:
    """
    Creates a directory

    Args:
        directory (str): path to create

    Returns:
        None
    """

    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError as e:
        # Raising any errors except concurrent access
        if e.errno != 17:
            raise


def get_other_extension(filename: str, target_extension: str) -> str:
    """
    Returns the filename given as argument with another extension (given as argument)

    Args:
        filename (str): filename to modify
        target_extension (str): new extension

    Returns:
        str: filename with new extension

    """

    basename, extension = os.path.splitext(filename)

    return "{0}.{1}".format(basename, target_extension)


def remove_abs(path: str) -> str:
    """
    Remove leading slash from path

    Args:
        path (str): path from which the leading slash must be removed

    Returns:
        str: path without leading slash

    """

    if os.path.isabs(path):
        return path.lstrip("/")
    else:
        return path
