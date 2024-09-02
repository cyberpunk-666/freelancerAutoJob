from app import create_app
from flask import Blueprint, render_template, redirect, url_for, flash

app = create_app()


@app.route('/')
def root():
    return redirect(url_for('jobs.index'))

if __name__ == '__main__':
    app.run(debug=True)
