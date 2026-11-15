"""
LINE MUSIC - NOT COLLECTED

Unable to do for this reason:
LINE MUSIC (Japan) shows its rankings only inside its app and to logged-in
users. There's no public chart page on music.line.me with the data in it, no
documented API, and no public feed. Collecting it would mean automating the
logged-in app, which breaks LINE's terms of use.
"""
from common import PlatformUnavailable

REASON = ("Unable to do for this reason: "
          "LINE MUSIC (Japan) shows its rankings only inside its app and to logged-in users. There's no public chart page on music.line.me with the data in it, no documented API, and no public feed. Collecting it would mean automating the logged-in app, which breaks LINE's terms of use.")


def fetch():
    raise PlatformUnavailable(REASON)
