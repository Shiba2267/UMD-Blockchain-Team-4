"""
iHeartRadio - NOT COLLECTED

Unable to do for this reason:
iHeartRadio is mainly a radio network, not an on-demand chart service. It
doesn't publish a live song chart: what it releases are year-end lists (in
press releases) and the "iHeartRadio Countdown" radio show. There is no chart
page or feed to collect from.
"""
from common import PlatformUnavailable

REASON = ("Unable to do for this reason: "
          'iHeartRadio is mainly a radio network, not an on-demand chart service. It doesn\'t publish a live song chart: what it releases are year-end lists (in press releases) and the "iHeartRadio Countdown" radio show. There is no chart page or feed to collect from.')


def fetch():
    raise PlatformUnavailable(REASON)
