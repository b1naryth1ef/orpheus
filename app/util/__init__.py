from flask import flash, redirect

def flashy(m, f="danger", u="/"):
    flash(m, f)
    return redirect(u)

