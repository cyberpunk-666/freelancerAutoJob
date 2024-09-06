from app import create_app
from flask import Blueprint, render_template, redirect, url_for, flash
import logging
from app.config.config import setup_logging
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
import os

setup_logging()
app = create_app()

Talisman(app, content_security_policy=None)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

@app.route('/')
def root():
    return redirect(url_for('jobs.index'))

if __name__ == '__main__':
    app.logger.info("Starting app...")
    # Run the app
    if os.getenv('FLASK_ENV') == 'development':
        # Run the app in debug mode
        app.run(ssl_context=('cert.pem', 'key_unencrypted.pem'), debug=True, use_reloader=False)
    else:
        app.run(debug=False)
