"""
Anghami - NOT COLLECTED

Unable to do for this reason:
Anghami does have charts and an official API for them
(sdk.anghami.com - "BrowseCharts" and "GetChartEntries"), but it requires a
partner API key (x-api-key) issued by Anghami to business partners. There's no
self-serve sign-up. If you ever get a key, this file can be written properly.
"""
from common import PlatformUnavailable

REASON = ("Unable to do for this reason: "
          'Anghami does have charts and an official API for them (sdk.anghami.com - "BrowseCharts" and "GetChartEntries"), but it requires a partner API key (x-api-key) issued by Anghami to business partners. There\'s no self-serve sign-up. If you ever get a key, this file can be written properly.')


def fetch():
    raise PlatformUnavailable(REASON)
