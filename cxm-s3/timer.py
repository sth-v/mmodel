#  Copyright (c)  CONTEXTMACHINE 2022.
#  AEC, computational geometry, digital engineering and Optimizing construction processes.
#
#  Author: Andrew Astakhov <sthv@contextmachine.space>
#
#  Computational Geometry, Digital Engineering and Optimizing your construction processes
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 2 of the License, or (at your
#  option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
#  the full text of the license.
#
#
#
import time
from datetime import date

from colored import attr, fg


class Timer(object):
    """
    Basic immutable class fixing the initialisation time
    >>> t = Timer()

    >>> t()

    >>> t.date_tag

    >>> t.hours, t.minutes

    """
    TIME_SIGN = [3, 4, 5]

    def __init__(self):
        _ts = self.__class__.TIME_SIGN
        _init_date = date.today().isoformat()

        _init_time = [time.gmtime()[i] for i in range(len(time.gmtime()))]
        _hours, _minutes, _secs = [_init_time[i] for i in _ts]
        self.date_tag = int(_init_date.replace('-', '')[2:], 10)
        self.hours = '0{}'.format(_hours) if len(str(_hours)[:2]) == 1 else str(_hours)
        self.minutes = '0{}'.format(_minutes) if len(str(_minutes)[:2]) == 1 else str(_minutes)
        self.seconds = '0{}'.format(_secs) if len(str(_secs)[:2]) == 1 else str(_secs)

    def __str__(self):
        return f"{fg('#49B0CE')}{self.date_tag} {self.hours}:{self.minutes}.{self.seconds}{attr('reset')}"

    def __call__(self):
        return self.date_tag, self.hours, self.minutes, self.seconds
