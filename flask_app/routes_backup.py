from datetime import date, datetime, timedelta

import requests
import os
from operator import itemgetter
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_app import app, db, encrypt, mail
# import forms
from flask_app.forms import (CreateComponent, CreateMovement, CreateWorkout,
                             LoginForm, RegistrationForm, ScoreComponents, ResetRequest,
                             PasswordReset, UpdateMovement, AccountUpdate)
from flask_app.helpers import send_reset_email, save_pic
from flask_bcrypt import generate_password_hash
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from sqlalchemy import desc, func

# import models
from .models import (BenchmarkScores, ComponentMovements, Components,
                     GeneralScores, Movements, Users, UserTestScores, Workouts)


@app.route('/workouts')
@login_required
def workouts():
    # get all workouts
    workouts = Workouts.query.filter(func.date(
        Workouts.date) <= date.today()).order_by(desc(Workouts.date)).all()
    for workout in workouts:
        # convert date to proper format
        workout.date = workout.date.date()
    return render_template('home.html', workouts=workouts)


@app.route('/workout/<wod_id>/detail')
@login_required
def workout_details(wod_id):
    # grab workouts and components
    workout = Workouts.query.get(wod_id)
    wod_date = workout.date.strftime('%Y-%m-%d')
    components = workout.components
    # init dictionary for user scores
    component_scores = {}
    # iterate through each of the days components
    for comp in components:
        print(comp.id)
        print(GeneralScores.query.filter_by(component_id=comp.id).all())
        # iterate through each movement in each component
        scores = GeneralScores.query.filter_by(component_id=comp.id).all()
        for score in scores:
            if score:
                user = Users.query.get(score.user_id)
                print(user)
                c = Components.query.get(score.component_id)
                print(c.description)
                if user not in component_scores.keys():
                    component_scores[user] = [
                        {'score': score.score, 'score_type': score.score_type, 'description': c.description}]
                    print('compontnet scores', user,  component_scores[user])
                else:
                    component_scores[user].append(
                        {'score': score.score, 'score_type': score.score_type, 'description': c.description})

    return render_template('workout_details.html', wod_date=wod_date, workout=workout, user=current_user,  component_scores=component_scores)


@app.route('/delete/<score_id>/<comp_id>', methods=['post', 'get'])
@login_required
def delete_score(score_id, comp_id):
    score = UserTestScores.query.get(score_id)
    if score.user_id == current_user.id:
        db.session.delete(score)
        db.session.commit()
        flash('score was deleted')
        return redirect(url_for('component_detail', comp_id=comp_id))
    else:
        flash('score was not deleted')
        return redirect(url_for('component_detail', comp_id=comp_id))


@app.route('/component/<comp_id>/detail', methods=['Post', 'Get'])
@login_required
def component_detail(comp_id):
    component = Components.query.get(comp_id)
    # print(type(component.movements[0]))
    wod = Workouts.query.get(component.wod_id)
    wod_date = wod.date.strftime('%Y-%m-%d')
    form = ScoreComponents()
    if form.validate_on_submit():
        comp = Components.query.get(comp_id)
        score = GeneralScores(component_id=comp_id, user_id=current_user.id,
                              score=form.score.data, score_type=form.score_type.data, notes=form.notes.data)
        db.session.add(score)

        if comp.is_test:
            move = component.movements[0]
            print('test: ', move, move.id)
            test_score = UserTestScores(
                move_id=move.move_id, user_id=current_user.id, score=form.score.data, score_type=form.score_type.data, test_day=date.today(), notes=form.notes.data)
            db.session.add(test_score)

        if comp.is_benchmark:
            benchmark_score = BenchmarkScores(
                component_id=comp_id, user_id=current_user.id, score=form.score.data, score_type=form.score_type.data)
            db.session.add(benchmark_score)

        db.session.commit()
        flash("Workout Scored!")
        return redirect(url_for('workout_details', wod_id=wod.id))
    component_scores = {}
    # print(current_user.movement_scores)

    for move in component.movements:
        movement = Movements.query.get(move.move_id)
        # grab last 5 scores for movement by current_user
        scores = UserTestScores.query.filter_by(
            move_id=movement.id).filter_by(user_id=current_user.id)[-5:]
        for score in scores:
            # check if already have scores in dict if not add it
            if movement.name not in component_scores.keys():
                component_scores[movement.name] = []
            # check for score type and add appropriate score values to dict
            if score.score_type == 'reps':
                component_scores[movement.name].append({
                    'total': score.score,
                    'metcon': score.score // 5,
                    'type': score.score_type,
                    'notes': score.notes,
                    'date': score.test_day,
                    'id': score.id
                })
            elif score.score_type == 'lbs':
                component_scores[movement.name].append({
                    'total': score.score,
                    'metcon': score.score * .6,
                    'type': score.score_type + ' ( 5 rep max)',
                    'notes': score.notes,
                    'date': score.test_day,
                    'id': score.id
                })
        # sort dictionary by date to show most recent scores first
        for k in component_scores.keys():
            for i in component_scores[k]:
                # if no date due to migration from old database add place holder and notes
                if i['date'] == None:
                    i['date'] = date.today() - timedelta(days=720)
                    if i['notes'] == None:
                        i['notes'] = 'invalid date'
                    else:
                    i['notes'] += 'invalid date'
            component_scores[k] = sorted(
                component_scores[k], key=lambda s: s['date'], reverse=True)

    return render_template('component_detail.html', wod_date=wod_date, component_scores=component_scores, component=component, form=form)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        password = form.password.data
        password = password.encode('utf-8')
        hashed_pw = generate_password_hash(password, rounds=10).decode('utf-8')
        new_user = Users(name=form.name.data, username=form.username.data,
                         email=form.email.data, password=hashed_pw)
        flash(
            f"Account Created for {new_user.username} you are now able to log in!")
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('workouts'))

    return render_template('registration.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            password = form.password.data
            password.encode('utf-8')

            if encrypt.check_password_hash(user.password, password):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get("next")
                if next_page:
                    return redirect(next_page)
                else:
                    return redirect(url_for('account'))
            else:
                flash('Invalid Passord')
                return redirect(url_for('login'))
        else:
            flash('No user with that email')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/account', methods=['post', 'get'])
@login_required
def account():
    user = current_user
    form = AccountUpdate()
    if form.validate_on_submit():
        print(form.name.data)
        user.name = form.name.data
        user.username = form.username.data
        email = form.email.data
        print(form.profile_pic.data, ' <--')
        if form.profile_pic.data:
            if user.profile_pic != 'default.jpg':
                old_pic = app.root_path + '/static/profile_pics/' + user.profile_pic
                print(old_pic, '<-- old')
            profile_pic = save_pic(form.profile_pic.data)
            user.profile_pic = profile_pic
            try:
                os.remove(old_pic)
            except FileNotFoundError:
                print('file not found')
            print(profile_pic)
        db.session.commit()
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.name.data = user.name
        form.username.data = user.username
        form.email.data = user.email

    image = url_for('static', filename=f'profile_pics/{user.profile_pic}')

    workout = Workouts.query.filter(
        func.date(Workouts.date) == date.today()).first()
    return render_template('account.html', form=form, image=image, workout=workout)


@app.route('/upcomingworkouts')
@login_required
def upcoming_workouts():
    workouts = (
        Workouts.query.filter(
            func.date(Workouts.date) >= (datetime.utcnow().date())
        )
        .order_by(Workouts.date)
        .limit(10)
    )
    month = datetime.utcnow().strftime("%B")
    return render_template(
        "upcoming_workouts.html", title="Upcoming Workouts", workouts=workouts, month=month
    )


@app.route('/reset_request', methods=['post', 'get'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("workouts"))
    form = ResetRequest()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if form.email.data == user.email:
                send_reset_email(user)
                return redirect(url_for('login'))
            else:
                flash('incorrect email')
                return redirect(url_for('reset_request'))
        else:
            flash('cannot find user with this username')
            return redirect(url_for('reset_request'))
    return render_template('reset_request.html', form=form)


@app.route('/reset_password/<token>', methods=['post', 'get'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("login"))
    user = Users.verify_reset_token(token)
    if not user:
        flash("invalid or expired token", "warning")
        return redirect(url_for("reset_request"))
    form = PasswordReset()
    if form.validate_on_submit():
        hashed_password = encrypt.generate_password_hash(form.password.data, rounds=10).decode(
            "utf-8"
        )
        user.password = hashed_password
        db.session.commit()
        flash(
            f"Account Updated for {user} you are now able to log in!", "success")
        return redirect(url_for("login"))
    return render_template("reset_password.html", title="Reset Password", form=form, token=token)


@app.route('/createworkout', methods=['post', 'get'])
def create_workout():
    if current_user.is_admin:
        form = CreateWorkout()

        if form.is_submitted():
            workout = Workouts(date=form.date.data)
            db.session.add(workout)
            db.session.commit()
            return redirect(url_for('create_component', wod_id=workout.id))
        return render_template('create_workout.html', form=form)
    else:
        flash('You must be an admin to create workouts')
        return redirect('/')


def update_workout(wod_id):
    workout = Workouts.query.get(wod_id)
    return redirect(url_for('create_component', wod_id=workout.id))


@app.route('/deleteworkout/<wod_id>')
def delete_workout(wod_id):
    if current_user.is_admin:
        workout = Workouts.query.get(wod_id)
        for comp in workout.components:
            for score in GeneralScores.query.all():
                if score.component_id == comp.id:
                    db.session.delete(score)
            for bmscore in BenchmarkScores.query.all():
                if score.component_id == comp.id:
                    db.session.delete(bmscore)
            for item in ComponentMovements.query.all():
                if item.component_id == comp.id:
                    db.session.delete(item)
            db.session.delete(comp)
        db.session.delete(workout)
        db.session.commit()
        return redirect(url_for('workouts'))
    else:
        flash('You must be an admin to delete workouts')
        return redirect('/')


@app.route('/createworkout/<wod_id>', methods=['Post', 'Get'])
def create_component(wod_id):
    # grab workout
    workout = Workouts.query.get(wod_id)
    # init form
    form = CreateComponent()
    if form.is_submitted():
        # create component
        component = Components(wod_id=wod_id, name=form.name.data, description=form.description.data,
                               is_test=form.is_test.data, is_benchmark=form.is_benchmark.data)
        db.session.add(component)
        db.session.commit()
        # create move relationship for componenmt
        for move in form.movements.data:
            for movement in Movements.query.all():
                if movement.name == move:
                    print(movement)
                    print(movement.id)
                    m = ComponentMovements(
                        move_id=movement.id, component_id=component.id)
                    print(m)
                    db.session.add(m)
                    db.session.commit()
        db.session.commit()
        return redirect(url_for('create_component', wod_id=workout.id))
    return render_template('create_component.html', workout=workout, form=form)


@app.route('/component/<comp_id>/update', methods=['post', 'get'])
def update_component(comp_id):
    form = CreateComponent()
    component = Components.query.get(comp_id)
    if form.is_submitted():
        if form.name.data:
            component.name = form.name.data
        if form.description.data:
            component.description = form.description.data
        if form.is_test.data:
            component.is_test = form.is_test.data
        if form.is_benchmark.data:
            component.is_benchmark = form.is_benchmark.data
        if form.movements.data:
            for move in form.movements.data:
                for movement in Movements.query.all():
                    if movement.name == move:
                        m = ComponentMovements(
                            move_id=movement.id, component_id=component.id)
                        db.session.add(m)
                        db.session.commit()

        db.session.commit()
        return redirect(url_for('component_detail', comp_id=comp_id))
    return render_template('update_component.html', component=component, form=form)


@app.route('/component/<comp_id>/delete')
def delete_component(comp_id):
    component = Components.query.get(comp_id)
    wod = Workouts.query.get(component.wod_id)
    for entry in component.movements:
        db.session.delete(entry)
    db.session.delete(component)
    db.session.commit()
    return redirect(url_for('workout_details', wod_id=wod.id))


@app.route('/createmovement', methods=['post', 'get'])
def create_movement():
    form = CreateMovement()
    movements = Movements.query.all()
    if form.validate_on_submit():
        for move in movements:
            if move.name == form.name.data:
                flash('Movement already exists')
                return redirect(url_for('create_movement'))
        move = Movements(name=form.name.data, upper=form.upper.data, lower=form.lower.data,
                         full=form.full.data, push=form.push.data, total=form.total.data, kind=form.kind.data)
        db.session.add(move)
        db.session.commit()
        return redirect(url_for('create_movement'))

    return render_template('create_movement.html', form=form, movements=movements)


@app.route('/movement/<move_id>/update', methods=['post', 'get'])
def update_movement(move_id):
    form = UpdateMovement()
    move = Movements.query.get(move_id)
    if form.is_submitted():
        move.name = form.name.data
        move.upper = form.upper.data
        move.lower = form.lower.data
        move.full = form.full.data
        move.push = form.push.data
        move.pull = form.pull.data
        move.total = form.total.data
        move.kind = form.kind.data
        db.session.commit()
        return redirect(url_for('create_movement'))
    elif request.method == 'GET':
        form.name.data = move.name
        form.upper.data = move.upper
        form.lower.data = move.lower
        form.full.data = move.full
        form.push.data = move.push
        form.pull.data = move.pull
        form.total.data = move.total
        form.kind.data = move.kind
    return render_template('update_movement.html', form=form, move=move)


@app.route('/coachboard')
def coachboard():
    if current_user.is_admin:
        athletes = Users.query.all()
        workout = Workouts.query.filter(func.date(
            Workouts.date) == date.today()).first()
        print(workout)
        components = [comp for comp in workout.components]
        print(components)
        scores = {}
        for athlete in athletes:
            scores[athlete] = []
            for comp in components:
                try:
                    scores[athlete].append(
                        {
                            'description': comp.description,
                            'score': GeneralScores.query.filter_by(user_id=athlete.id).filter_by(component_id=comp.id).first().score,
                            'score_type': GeneralScores.query.filter_by(user_id=athlete.id).filter_by(component_id=comp.id).first().score_type
                        }
                    )
                except:
                    print('no score')

    else:
        flash('you must be a coach to access this page')
        return redirect(url_for('login'))
    return render_template('coachboard.html', scores=scores, components=components)


def coachboard_detail(user_id, comp_id):
    user = Users.query.get(user_id)
    form = ScoreComponents()
    if form.validate_on_submit():
        comp = Components.query.get(comp_id)
        score = GeneralScores(component_id=comp_id, user_id=user.id,
                              score=form.score.data, score_type=form.score_type.data, notes=form.notes.data)
        db.session.add(score)

        if comp.is_test:
            move = component.movements[0]
            print('test: ', move, move.id)
            test_score = UserTestScores(
                move_id=move.move_id, user_id=current_user.id, score=form.score.data, score_type=form.score_type.data, test_day=date.today(), notes=form.notes.data)
            db.session.add(test_score)

        if comp.is_benchmark:
            benchmark_score = BenchmarkScores(
                component_id=comp_id, user_id=current_user.id, score=form.score.data, score_type=form.score_type.data)
            db.session.add(benchmark_score)

        db.session.commit()
        flash("Workout Scored!")
        return redirect(url_for('workout_details', wod_id=wod.id))
