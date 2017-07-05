import os
from shutil import rmtree
import subprocess

_updatedGitRepos = []
"""A Cache for all repositories which have been updated
during the runtime of this program. We don't want them
updating during commands.
"""


def isInitalized(repoPath):
    """>>> isInitialized(repoPath) -> boolean
    Returns true if there is an initialized repository in
    the given path 'repopath'.
    """
    return os.path.isdir(os.path.join(repoPath, '.git'))


def update(gitPath, repoDir, logger):
    """>>> update(gitpath, repoDir, logger) -> success
    Updates the repository in 'repoPath', so it
    is at the same state as the origin, using the
    git executable at 'gitPath'.
    """
    if repoDir in _updatedGitRepos:
        return True
    _updatedGitRepos.append(repoDir)
    args = [gitPath, '-C', repoDir, 'fetch', 'origin']
    logger.verbose('Calling ' + subprocess.list2cmdline(args))
    if subprocess.call(args) != 0:
        return False
    args = [gitPath, '-C', repoDir, 'reset', '--hard', 'origin/master']
    logger.verbose('Calling ' + subprocess.list2cmdline(args))
    if subprocess.call(args) != 0:
        return False
    args = [gitPath, '-C', repoDir, 'clean', '-d', '-f']
    logger.verbose('Calling ' + subprocess.list2cmdline(args))
    if subprocess.call(args) != 0:
        return False
    args = [gitPath, '-C', repoDir, 'pull']
    logger.verbose('Calling ' + subprocess.list2cmdline(args))
    return subprocess.call(args) == 0


def initialize(gitPath, repoUrl, repoDir, logger):
    """>>> initialize(gitPath, repoUrl, repoDir, logger) -> success
    Initializes and clones the repository from 'repoUrl'
    to 'repoDir', using the git executable at 'gitPath'.
    Returns True on success and False on failure.
    """
    if os.path.exists(repoDir):
        if not os.path.isdir(repoDir):
            logger.error('Failed to initialize the repository from "' + repoUrl +
                         '" to "' + repoDir + '": The destination is an existing file!')
            return False
        rmtree(repoDir)
    args = [gitPath, 'clone', '--progress', repoUrl, repoDir]
    logger.verbose('Calling ' + subprocess.list2cmdline(args))
    if subprocess.call(args) == 0:
        return True
        args = [gitPath, '--work-tree', repoDir, 'pull']
        logger.verbose('Calling ' + subprocess.list2cmdline(args))
        return subprocess.call(args)
    return False
