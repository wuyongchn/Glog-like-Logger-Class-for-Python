import logging
import time
import traceback
import os


# Those are ANSI escape codes, which you can read look up on Google,
# or find here: en.wikipedia.org/wiki/ANSI_escape_code,
# or alternatively pueblo.sourceforge.net/doc/manual/ansi_color_codes.html

# The background is set with 40 plus the number of the color,
# and the foreground with 30
class _ANSIColor(object):
    def __init__(self):
        pass
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)


# These are the sequences need to get colored output
class _Seq(object):
    def __init__(self):
        pass
    RESET_SEQ = '\033[0m'
    COLOR_SEQ = '\033[1;%dm'


class _LogColoredFormatter(logging.Formatter):

    def __init__(self):
        super(_LogColoredFormatter, self).__init__()
        self._level_map = {
            logging.INFO: 'I',
            logging.WARNING: 'W',
            logging.ERROR: 'E',
            logging.FATAL: 'F',
            logging.DEBUG: 'D'}

        self._colors = {
            'INFO': _ANSIColor.WHITE,
            'WARNING': _ANSIColor.YELLOW,
            'ERROR': _ANSIColor.RED,
            'FATAL': _ANSIColor.RED,
            'CRITICAL': _ANSIColor.RED,
            'DEBUG': _ANSIColor.BLUE}

    def format(self, record):
        try:
            level = self._level_map[record.levelno]
        except KeyError:
            level = '?'
        date = time.localtime(record.created)
        date_usec = (record.created - int(record.created)) * 1e6
        record_message = '%c%02d%02d %02d:%02d:%02d.%06d %s %s:%d] %s' % (
            level, date.tm_mon, date.tm_mday, date.tm_hour, date.tm_min,
            date.tm_sec, date_usec,
            record.process if record.process is not None else '????',
            record.filename,
            record.lineno,
            self._format_message(record))
        record_message_color = _Seq.COLOR_SEQ % (30 + self._colors[record.levelname]) + record_message + _Seq.RESET_SEQ

        record.getMessage = lambda: record_message_color
        return logging.Formatter.format(self, record)

    @staticmethod
    def _format_message(record):
        try:
            record_message = '%s' % (record.msg % record.args)
        except TypeError:
            record_message = record.msg
        return record_message


class Logger(object):
    def __init__(self):
        self._logger = logging.getLogger()
        self._console = logging.StreamHandler()
        self._console.setFormatter(_LogColoredFormatter())
        self._logger.addHandler(self._console)
        self.set_default_level()
        self._level_names = {
            logging.INFO: 'INFO',
            logging.WARNING: "WARNING",
            logging.ERROR: 'ERROR',
            logging.FATAL: 'FATAL',
            logging.DEBUG: 'DEBUG'}
        self._level_letters = [name[0] for name in self._level_names.values()]

        self.info = logging.info
        self.warning = logging.warning
        self.error = logging.error
        # fatal method reimplenmented
        self.debug = logging.debug

    def set_default_level(self):
        self._logger.setLevel(logging.INFO)

    def set_level(self, new_level):
        self._logger.setLevel()
        self._logger.setLevel(new_level)
        self._logger.debug('Log level set to %s', new_level)

    # Define functions emulating C++ glog check-macros
    # https://htmlpreview.github.io/?https://github.com/google/glog/master/doc/glog.html#check
    # python code from https://github.com/benley/python-glog/blob/master/glog.py
    @staticmethod
    def _format_stacktrace(stack):
        """Print a stack trace that is easier to read.
        Reduce paths to basename component
        Truncates the part of the stack after the check failure
        """
        lines = []
        for _, f in enumerate(stack):
            fname = os.path.basename(f[0])
            line = '%s:%d    %s' % (fname + '::' + f[2], f[1], f[3])
            lines.append(line)
        return lines

    class FailedCheckException(AssertionError):
        """Exception with message indicating check-failure location and values"""
    def fatal(self, msg=None):
        stack = traceback.extract_stack()
        filename, lineno, _, _ = stack[-2]
        try:
            raise self.FailedCheckException(msg)
        except self.FailedCheckException:
            log_record = self._logger.makeRecord(
                'CRITICAL', 50, filename, lineno, msg, None, None)
            self._console.handle(log_record)
            raise

    @staticmethod
    def _get_args(string, tag):
        def _delete_pre_and_last_blank(_arg):
            while _arg[0] == ' ':
                _arg = _arg[1:]
            while _arg[-1] == ' ':
                _arg = _arg[:-1]
            return _arg

        start_idx = string.find('(')
        if tag is None:
            end_idx = string.rfind(')')
        else:
            end_idx = string.rfind(',', 0, string.find(tag))
        arg = string[start_idx+1:end_idx]
        comma_idx = arg.find(',')
        if comma_idx == -1:
            arg = _delete_pre_and_last_blank(arg)
        else:
            arg1 = _delete_pre_and_last_blank(arg[:comma_idx])
            arg2 = _delete_pre_and_last_blank(arg[comma_idx+1:])
            arg = (arg1, arg2)
        return arg

    def _check_failed(self, msg):
        stack = traceback.extract_stack()
        stack = stack[0:-2]
        filename, lineno, _, args = stack[-1]
        arg = self._get_args(args, msg[-1])
        if isinstance(arg, str):
            if msg[-1] is None:
                msg = msg[0] + arg
            else:
                msg = msg[0] + arg + ' ' + msg[1]
        else:
            if msg[-1] is None:
                msg = msg[0] + arg[0] + msg[1] + arg[1] + msg[2]
            else:
                msg = msg[0] + arg[0] + msg[1] + arg[1] + msg[2] + msg[3]

        try:
            raise self.FailedCheckException(msg)
        except self.FailedCheckException:
            log_record = self._logger.makeRecord(
                'CRITICAL', 50, filename, lineno, msg, None, None)
            self._console.handle(log_record)
            raise

    def check(self, condition, msg=None):
        """Raise exception with message if condition is false."""
        if not condition:
            msg = ('Check failed: ', msg)
            self._check_failed(msg)

    def check_eq(self, obj1, obj2, msg=None):
        """Raise exception with message if object1 != object2."""
        if obj1 != obj2:
            msg = ('Check failed: ', ' == ', ' (' + str(obj1) + ' vs. ' + str(obj2) + ') ', msg)
            self._check_failed(msg)

    def check_ne(self, obj1, obj2, msg=None):
        """Raise exception with message if obj1 == obj2."""
        if obj1 == obj2:
            msg = ('Check failed: ', ' != ', ' (' + str(obj1) + ' vs. ' + str(obj2) + ') ', msg)
            self._check_failed(msg)

    def check_le(self, obj1, obj2, msg=None):
        """Raise exception with message if not (obj1 <= obj2.)"""
        if obj1 > obj2:
            msg = ('Check failed: ', ' <= ', ' (' + str(obj1) + ' vs. ' + str(obj2) + ') ', msg)
            self._check_failed(msg)

    def check_ge(self, obj1, obj2, msg=None):
        """Raise exception with message if not (obj1 >= obj2.)"""
        if obj1 < obj2:
            msg = ('Check failed: ', ' >= ', ' (' + str(obj1) + ' vs. ' + str(obj2) + ') ', msg)
            self._check_failed(msg)

    def check_lt(self, obj1, obj2, msg=None):
        """Raise exception with message if not (obj1 < obj2.)"""
        if obj1 >= obj2:
            msg = ('Check failed: ', ' < ', ' (' + str(obj1) + ' vs. ' + str(obj2) + ') ', msg)
            self._check_failed(msg)

    def check_gt(self, obj1, obj2, msg=None):
        """Raise exception with message if not (obj1 > obj2.)"""
        if obj1 <= obj2:
            msg = ('Check failed: ', ' > ', ' (' + str(obj1) + ' vs. ' + str(obj2) + ') ', msg)
            self._check_failed(msg)


log = Logger()

if __name__ == '__main__':
    log.info('this is log info')
    log.warning('this is log info')
    log.error('this is log info')
    # log.fatal('this is log info')

    a = 1; b = 2
    log.check(type(a)==float)

    log.check(type(a)==float, "this's ts")
    log.check(type(a)==float, 'this is a check')

    log.check_eq(type(a), float)
    log.check(a == b, 'this is log check')
    log.check_eq(type(a), float, "this's lg check_eq")
    log.check_ne(a+1, b, 'this is log check_ne')
    log.check_ge(a, b, 'this is log check_ge')
    log.check_le(a+2, b, 'this is log check_le')
    log.check_gt(a, b, 'this is log check_gt')
    log.check_lt(a+1, b, 'this is log check_lt')
