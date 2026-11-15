"""
Instagram - NOT COLLECTED

Unable to do for this reason:
Instagram has no music chart. "Trending audio" for Reels is only shown
inside the mobile app, personalised to each user. There is no public page,
feed or API for it, and Meta actively blocks automated access to Instagram.
Its official API (Graph API) only covers business accounts you manage.
"""
from common import PlatformUnavailable

REASON = ("Unable to do for this reason: "
          'Instagram has no music chart. "Trending audio" for Reels is only shown inside the mobile app, personalised to each user. There is no public page, feed or API for it, and Meta actively blocks automated access to Instagram. Its official API (Graph API) only covers business accounts you manage.')


def fetch():
    raise PlatformUnavailable(REASON)
