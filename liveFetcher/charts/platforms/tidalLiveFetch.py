"""
TIDAL - NOT COLLECTED

Unable to do for this reason:
TIDAL's official developer API (openapi.tidal.com) gives free keys for
catalog data (songs, albums, artists), but it has no charts endpoint. TIDAL's
charts exist only as editorial playlists, and reading playlist contents through
the official API has needed a logged-in user. The unofficial route (copying
keys out of TIDAL's own apps) breaks TIDAL's developer terms.
"""
from common import PlatformUnavailable

REASON = ("Unable to do for this reason: "
          "TIDAL's official developer API (openapi.tidal.com) gives free keys for catalog data (songs, albums, artists), but it has no charts endpoint. TIDAL's charts exist only as editorial playlists, and reading playlist contents through the official API has needed a logged-in user. The unofficial route (copying keys out of TIDAL's own apps) breaks TIDAL's developer terms.")


def fetch():
    raise PlatformUnavailable(REASON)
