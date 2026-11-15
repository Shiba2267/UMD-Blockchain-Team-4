"""
Amazon Music - NOT COLLECTED

Unable to do for this reason:
There is no public, supported way to read Amazon Music's charts.
  * The official Amazon Music Web API is invite-only: you must apply to
    Amazon and be approved, and its "top tracks" endpoint requires that access.
  * The charts page (music.amazon.com/popular) can be viewed without signing in,
    but it's drawn by the web player from Amazon's internal requests, which carry
    session tokens the player creates. Copying that would mean automating a
    browser, which is fragile, and Amazon's Conditions of Use forbid robots
    and data-gathering tools on its sites.
"""
from common import PlatformUnavailable

REASON = ("Unable to do for this reason: "
          'There is no public, supported way to read Amazon Music\'s charts. * The official Amazon Music Web API is invite-only: you must apply to Amazon and be approved, and its "top tracks" endpoint requires that access. * The charts page (music.amazon.com/popular) can be viewed without signing in, but it\'s drawn by the web player from Amazon\'s internal requests, which carry session tokens the player creates. Copying that would mean automating a browser, which is fragile, and Amazon\'s Conditions of Use forbid robots and data-gathering tools on its sites.')


def fetch():
    raise PlatformUnavailable(REASON)
