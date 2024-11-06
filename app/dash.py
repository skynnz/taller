from flask import Blueprint, render_template
from .auth import login_required

bp = Blueprint('dash', __name__, url_prefix='/dash')

@bp.route('/')
@login_required
def index():
    return render_template('dashboard.html')