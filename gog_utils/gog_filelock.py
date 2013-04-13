"""
This filelock module has been taken and modified from
www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/
Thanks to Evan Fosmark for this code.
"""


import os
import time
import errno


class FileLockException(Exception):
    """ Class for FileLock exception type. """
    pass


class FileLock(object):
    """
    A file locking mechanism that has context-manager support so
    you can use it in a with statement. This should be relatively cross
    compatible as it doesn't rely on msvcrt or fcntl for the locking.
    """

    def __init__(self, file_name, path, timeout=10, delay=.05):
        """
        Prepare the file locker. Specify the file to lock, the path
        and optionally the maximum timeout and the delay between
        each attempt to lock.
        """
        self.is_locked = False
        if not os.path.exists(path):
            os.makedirs(path)
        self.lockfile = os.path.join(path, "%s.lock" % file_name)
        self.file_name = file_name
        self.timeout = timeout
        self.delay = delay

    def acquire(self):
        """
        Acquire the lock, if possible. If the lock is in use, it check again
        every `wait` seconds. It does this until it either gets the lock or
        exceeds `timeout` number of seconds, in which case it throws
        an exception.
        """
        start_time = time.time()
        while True:
            try:
                self.file_handle = os.open(self.lockfile,
                                           os.O_CREAT | os.O_EXCL | os.O_RDWR)
                break
            except OSError as err:
                if err.errno != errno.EEXIST:
                    raise
                if (time.time() - start_time) >= self.timeout:
                    raise FileLockException("Timeout occured.")
                time.sleep(self.delay)
        self.is_locked = True

    def release(self):
        """
        Get rid of the lock by deleting the lockfile.
        When working in a `with` statement, this gets automatically
        called at the end.
        """
        if self.is_locked:
            os.close(self.file_handle)
            os.unlink(self.lockfile)
            self.is_locked = False

    def __enter__(self):
        """
        Activated when used in the with statement.
        Should automatically acquire a lock to be used in the with block.
        """
        if not self.is_locked:
            self.acquire()
        return self

    def __exit__(self, type, value, traceback):
        """
        Activated at the end of the with statement.
        It automatically releases the lock if it isn't locked.
        """
        if self.is_locked:
            self.release()

    def __del__(self):
        """
        Make sure that the FileLock instance doesn't leave a
        lockfile lying around.
        """
        self.release()
