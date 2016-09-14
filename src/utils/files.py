import errno
import os
import shutil

def mkdirs(path):
    '''>>> mkdirs(path) -> success
    Create the directory 'path' and all its parent
    directories if necessary. Returns True, if the
    directory exists and False, if there was an error.
    '''
    try:
        os.makedirs(path)
    except OSError as exc:
        if not (exc.errno == errno.EEXIST and os.path.isdir(path)):
            return False
    return True

def deleteDir(dirPath):
    '''>>> deleteDir(dirPath) -> success
    Deletes the directory 'dirPath' and it's content.
    Returns True on success, False otherwise.
    '''
    if os.path.isdir(dirPath):
        MAX_TRIES = 3
        for i in range(MAX_TRIES):
            shutil.rmtree(dirPath, ignore_errors = False)
            if os.path.exists(dirPath):
                if i + 1 == MAX_TRIES:
                    return False
            else:
                break
            sleep(1)
    elif os.path.isfile(dirPath):
        return False
    return True
