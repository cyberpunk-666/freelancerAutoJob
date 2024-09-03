from app import create_app
from flask import Blueprint, render_template, redirect, url_for, flash
import logging
from app.config.config import setup_logging

app = create_app()
setup_logging()


@app.route('/')
def root():
    return redirect(url_for('jobs.index'))

if __name__ == '__main__':
    app.run(debug=True)
