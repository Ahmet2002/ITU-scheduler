from PyQt5.QtWidgets import QApplication
from course_scheduler import CourseScheduler

if __name__ == '__main__':
    app = QApplication([])
    window = CourseScheduler()
    window.show()
    app.exec_()