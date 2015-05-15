from flask import Blueprint, render_template, url_for, redirect, flash, request, current_app
from flask.ext.login import login_required, logout_user, current_user, login_user
from .forms import LoginForm, PasswordResetForm, PasswordResetSubmitForm
from school.config import FLASH_SUCCESS, FLASH_INFO, FLASH_WARNING, FLASH_ERROR
from school.user.models import User
from school.extensions import *
from flask.ext.mail import Message


frontend = Blueprint('frontend', __name__)


@frontend.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated():  # user is already logged in
        flash("You are already logged in", FLASH_WARNING)
        return redirect(url_for('user.index'))

    form = LoginForm()
    if form.validate_on_submit():
        if form.remember_me.data:
            login_user(form.user, remember=True)
        else:
            login_user(form.user)

        return form.redirect("user.index")

    return render_template('frontend/index.html', form=form)


@frontend.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', FLASH_INFO)

    return redirect(url_for("frontend.login"))


@frontend.route('/password_reset', methods=["GET", "POST"])
def password_reset():
    token = request.args.get('token')
    if token is None:
        password_reset_form = PasswordResetForm()
        if password_reset_form.validate_on_submit():
            email = password_reset_form.email.data
            user = User.query.filter_by(email=email).first()
            if user is not None:
                token = user.get_token()
                msg = Message('Reset password', sender='academicinfo.seproject@gmail.com', recipients=[email])
                msg.html = render_template('frontend/password_reset_email.html', user=user, token=token)
                mail.send(msg)
                return render_template('frontend/password_reset_confirmation_sent.html')
        return render_template('frontend/password_reset.html', form=password_reset_form)

    token = request.args.get('token', None)
    # a token was given
    verified_result = User.verify_token(token)

    # given token is not valid
    if verified_result is None:
        flash("It looks like you clicked on an invalid password reset link. Please try again.", FLASH_ERROR)
        password_reset_form = PasswordResetForm()
        return render_template('frontend/password_reset.html', form=password_reset_form)

    password_submit_form = PasswordResetSubmitForm()
    if password_submit_form.validate_on_submit():
        # after you enter the passwords the token will be None and the execution will enter the first if
        # so this code won't be executed.
        verified_result.password = password_submit_form.new_password.data
        verified_result.is_active = True
        db.session.add(verified_result)
        db.session.commit()
        flash("New password set successfully.", FLASH_SUCCESS)
        msg = Message('Your password has changed', sender='academicinfo.seproject@gmail.com', recipients=[verified_result.email])
        msg.html = render_template('user/changed_password_email.html', user=verified_result)
        mail.send(msg)
        return password_submit_form.redirect("user.index")
    return render_template('frontend/password_reset_submit.html', password_submit_form=password_submit_form)

