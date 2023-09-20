from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, flash
from datetime import datetime
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hemlig'  # Translated 'secret' to 'hemlig' in Swedish
socketio = SocketIO(app)

# Queue of students
queue = []


# Utility functions
def is_student_in_queue(student_name):
    return student_name in [s['name'] for s in queue]


# Routes related to joining and leaving the queue
@app.route('/', methods=['GET'])
def index():
    student_name = request.cookies.get('student_name')
    if is_student_in_queue(student_name):
        return redirect(url_for('waiting_page'))
    return render_template('index.html', queue_length=len(queue))


@app.route('/join', methods=['POST'])
def join_queue():
    student_name = request.cookies.get('student_name')
    if is_student_in_queue(student_name):
        flash("Du är redan i kön!", 'danger')
        return redirect(url_for('index'))

    student_name = request.form.get('name')
    if not student_name:
        flash("Namn krävs", 'danger')
        return redirect(url_for('index'))

    student = {
        "name": student_name,
        "joined_at": datetime.now()
    }
    queue.append(student)

    response = make_response(redirect(url_for('waiting_page')))
    response.set_cookie('student_name', student_name, max_age=60*60*24)  # Cookie expires after 24 hours

    for student in queue:
        if isinstance(student['joined_at'], datetime):
            student['joined_at'] = student['joined_at'].strftime('%Y-%m-%d %H:%M:%S')
    socketio.emit('queue_update', queue)

    flash("Du har gått med i kön!", 'success')
    return response


@app.route('/leave', methods=['POST', 'GET'])
def leave_queue():
    student_name = request.cookies.get('student_name')
    if not is_student_in_queue(student_name):
        flash("Du är inte i kön längre", 'danger')
        return redirect(url_for('index'))

    global queue
    queue = [student for student in queue if student['name'] != student_name]

    response = make_response(redirect(url_for('index')))
    response.delete_cookie('student_name')

    socketio.emit('queue_update', queue)
    return response


# Routes related to viewing the queue
@app.route('/waiting', methods=['GET'])
def waiting_page():
    student_name = request.cookies.get('student_name')
    if not is_student_in_queue(student_name):
        flash("Du är inte i kön!", 'danger')
        return redirect(url_for('index'))

    position = next((i for i, student in enumerate(queue) if student['name'] == student_name), None) + 1
    students_ahead = queue[:position-1]
    return render_template('waiting.html', position=position, students_ahead=students_ahead, name=student_name)


@app.route('/view_queue', methods=['GET'])
def view_queue():
    return render_template('queue.html', queue=queue)


@app.route('/remove_student', methods=['POST'])
def remove_student():
    student_name = request.form.get('student_name')
    global queue
    queue = [student for student in queue if student['name'] != student_name]

    socketio.emit('queue_update', queue)
    flash(f"Tog bort {student_name} från kön.", 'success')
    return redirect(url_for('view_queue'))


@app.route('/list', methods=['GET'])
def list_all():
    all_students = [student['name'] for student in queue]
    return render_template('list.html', all_students=all_students)
    

@app.route('/clear_queue', methods=['POST'])
def clear_queue():
    global queue
    queue = []
    return redirect(url_for('view_queue'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html'), 500


if __name__ == '__main__':
    socketio.run(app, debug=True)
