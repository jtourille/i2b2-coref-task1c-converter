import os


def ensure_dir(directory: str) -> None:
    """
    Creates a directory
    Args:
        directory: path to create
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
        filename: filename to modify
        target_extension: new extension

    Returns:
        str: filename with new extension

    """

    basename, extension = os.path.splitext(filename)

    return "{0}.{1}".format(basename, target_extension)
