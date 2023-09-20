from datetime import datetime

def estimate_wait_time(student, queue):
    time_in_queue = datetime.now() - student['joined_at']
    estimated_wait = len(queue) * 5 - time_in_queue.seconds // 60
    return max(0, estimated_wait)
