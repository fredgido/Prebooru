from flask import render_template

def DisplayArtists(artist_ids):
    if len(artist_ids) == 0:
        return "<em>No artists.</em>"
    return render_template("pools/_artist_list.html", artist_ids=artist_ids)

