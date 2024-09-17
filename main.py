from PyQt5.QtWidgets import QApplication
import qdarkstyle
from course_scheduler import CourseScheduler

if __name__ == '__main__':
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    window = CourseScheduler()
    window.show()
    app.exec_()