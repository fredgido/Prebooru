from flask import render_template

def Preview(post):
    return render_template("posts/_preview.html", post=post)
