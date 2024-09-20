from PyQt5.QtCore import QTime, QStringListModel
from bs4 import BeautifulSoup
from sortedcontainers import SortedDict
import json, os

class CourseSchedulerBackend:
    def __init__(self, parent, logger):
        self._config()
        self.parent = parent
        self.logger = logger
        self.conn = None
        self.student_major_id = 0
        self.allready_taken_class_codes = set()
        self.prerequisite_class_codes_set = set()
        self.selected_class_ids = []
        self.selected_class_code_names = []
        self.selected_class_code_names_set = set()
        self.excluded_time_blocks = set() # Holds (day, start_time, end_time) tuples. start_time & end_time in minutes
        self.results = [] # Holds lists of course ids each list being a result
        self.current_result_index = 0
        self.something_changed = True
        self.temp_results = [] # Temporary results so that we dont mess up the previous results if some problem occurs during the calculation
        self.potential_result = [] # Holds course ids
        self.courses = {}
        self.classes = {}
        self.majors = []
        self.professors = []
        self.class_id_to_course_ids_map = {}
        self.class_code_name_to_id_map = {}
        self.course_id_to_same_time_course_ids_map = {}
        self.class_code_to_class_ids_map = SortedDict()
        self.current_class_code = None
        self.added_classes = SortedDict()
        self.added_classes_model = QStringListModel()


    def _config(self):
        self.day_start_time = QTime(8, 30) # 8:30
        self.day_end_time = QTime(17, 30) # 17:30
        self.time_resolution = 15
        self.day_start_time_minutes = self._time_to_minutes(self.day_start_time) # 8:30
        self.day_end_time_minutes = self._time_to_minutes(self.day_end_time) # 17:30
        self.total_slot_limit = 15
        self.total_options_count_limit = 8
        self.state_file_addr = 'state.json'
        self.output_image_directory_path = 'output_images'
        # Error Messages
        self.ERROR_DB_NOT_EXIST = 'Class does not exist in the database.\nMake sure that you typed it right and the database is up to date'
        self.ERROR_PREREQ_NOT_EXIST = 'Class does not exist in amongst the prerequisites.\nMake sure that you typed it right and the database is up to date\nIf you are sure about these two\nIt means you dont need\nto care about this class for prerequisites'
        self.ERROR_NO_COMBINATION = 'Could not find any combinations satisfying the conditions.'
        self.ERROR_TIME_COLLISION = 'Time block must not collide with the previous time blocks'
        self.ERROR_CLASS_ALLREADY_EXIST = 'Class already exists.'
        self.ERROR_NOT_MULTIPLE_OF_RESOLUTION = f'Time Exclusion Block show be multiple of {self.time_resolution}'
        self.ERROR_PREREQS_NOT_SATISFIED = lambda class_id: f"Prerequisites are not satisfied.\nProblematic class is:{self.classes[class_id][0]}\nRequired Prerequisites are: {' and '.join('('+' or '.join(or_group)+')' for or_group in self.classes[class_id][2])}"
        self.ERROR_MAJOR_NOT_SELECTED = 'Major is not selected.\nPlease first select a major.'
        self.MESSAGE_CONFIRM_MAJOR_UPDATE = 'Updating the major will reset the selected classes\nredownload the related prerequisites and\nrefetch the related data from the database.\nDo you want to proceed?'
        self.MESSAGE_CONFIRM_DB_UPDATE = "Updating the database may take some time.\nAnd it will also reset the program state.\nSo don't use this button too frequently.\nDo you want to proceed?"
        self.MESSAGE_NOTHING_CHANGED = 'No parameter was changed.\nSo nothing to calculate.'


    def reset_state(self):
        self.student_major_id = 0
        self.selected_class_code_names = []
        self.selected_class_ids = []
        self.results = []
        self.course_id_to_same_time_course_ids_map = {}
        self.current_result_index = 0
        self.something_changed = True
        self.current_class_code = ''
        self.class_code_to_class_ids_map.clear()
        self.added_classes.clear()


    def save_state(self, file_addr):
        self.get_selected_class_code_names_from_slot_list()
        state = {
            'selected_class_code_names': self.selected_class_code_names,
            'allready_taken_class_codes': list(self.allready_taken_class_codes),
            'excluded_time_blocks': [[item for item in time_block] for time_block in self.excluded_time_blocks],
            'student_major_id': self.student_major_id,
            'course_id_to_same_time_course_ids_map': self.course_id_to_same_time_course_ids_map,
            'results': self.results,
            'current_result_index': self.current_result_index,
            'something_changed': self.something_changed,
            'current_class_code': self.current_class_code,
            'added_classes': dict(self.added_classes)
        }
    
        with open(file_addr, 'w') as f:
            json.dump(state, f, indent=4)

    def load_state(self, file_addr):
        if os.path.exists(file_addr):
            with open(file_addr, 'r') as file:
                state = json.load(file)

            self.selected_class_code_names = state.get('selected_class_code_names', [])
            self.allready_taken_class_codes = set(state.get('allready_taken_class_codes', []))
            self.student_major_id = state.get('student_major_id', 0)
            course_id_str_to_same_time_course_ids_map = state.get('course_id_to_same_time_course_ids_map', {})
            self.course_id_to_same_time_course_ids_map = {int(key): value for key, value in course_id_str_to_same_time_course_ids_map.items()}
            self.results = state.get('results', [])
            self.current_result_index = state.get('current_result_index', 0)
            self.something_changed = state.get('something_changed', True)
            self.excluded_time_blocks = set([tuple(int(item) for item in lst) for lst in state.get('excluded_time_blocks', [])])
            self.current_class_code = state.get('current_class_code', '')
            self.added_classes = SortedDict(state.get('added_classes', {}))
    

    def get_selected_class_code_names_from_slot_list(self):
        self.selected_class_code_names = [
            [class_code_name for class_code_name in slot_row.class_options] for slot_row in self.parent.slot_list_tab.slot_rows
            if slot_row.class_options != []
        ]


    def calculate_combinations(self):
        # check if the user has changed some parameter if nothing was changed then no need to recalculate
        if not self._is_it_allowed() or not self.something_changed:
            return
        
        # Map self.selected_class_ids from self.selected_class_code_names
        self.get_selected_class_code_names_from_slot_list()
        self.selected_class_ids = [[self.class_code_name_to_id_map[class_code_name] for class_code_name in slot] for slot in self.selected_class_code_names]

        # Prerequisites are allready checked at the class addition stage 
        
        # Filter not aplicable courses and duplicates in terms of day and time
        course_id_to_same_time_course_ids_map = {}
        courses = [[course_id for class_id in slot for course_id in self.class_id_to_course_ids_map.get(class_id, [])]
                   for slot in self.selected_class_ids]
        courses = [self._exclude_same_time_courses(course_ids, course_id_to_same_time_course_ids_map) for course_ids in courses]
        course_id_to_same_time_course_ids_map = {course_id: sorted(same_time_ids, key=lambda item: self.courses[item][4], reverse=True)
                                                for course_id, same_time_ids in course_id_to_same_time_course_ids_map.items()}

        self._calculate_results(courses)
        if self.temp_results == []:
            self.something_changed = False
            self.parent.show_warning(self.ERROR_NO_COMBINATION)
            return
        
        self.results = self.temp_results
        self.temp_results = []
        self.course_id_to_same_time_course_ids_map = course_id_to_same_time_course_ids_map
        self.current_result_index = 0
        self.something_changed = False # Reset the value of something_changed


    def add_excluded_time_block(self, block_tuple):
        if block_tuple[1] >= self.day_start_time_minutes and block_tuple[2] <= self.day_end_time_minutes:
            if self._collision_for_exclusion_time_blocks_ok(block_tuple):
                self.excluded_time_blocks.add(block_tuple)
                self.something_changed = True
                return True
            else:
                self.parent.show_warning(self.ERROR_TIME_COLLISION)
        else:
            self.parent.show_warning(f"Time block must be between {self.day_start_time}\
            and {self.day_end_time}")
        return False
    
    def remove_excluded_time_block(self, block_tuple):
        if block_tuple in self.excluded_time_blocks:
            self.excluded_time_blocks.remove(block_tuple)
            self.something_changed = True

    def add_to_allready_taken_class_codes(self, class_code):
        if not self._is_it_allowed() or class_code == '':
            return False
        
        if class_code in self.prerequisite_class_codes_set\
            or class_code + 'E' in self.prerequisite_class_codes_set:
            if class_code not in self.allready_taken_class_codes:
                self.allready_taken_class_codes.add(class_code)
                self.something_changed = True
                return True
            else:
                self.parent.show_warning(self.ERROR_CLASS_ALLREADY_EXIST)
        else:
            self.parent.show_warning(self.ERROR_PREREQ_NOT_EXIST)
        return False

    def remove_from_allready_taken_class_codes(self, class_code):
        if not self._is_it_allowed():
            return
        
        if class_code in self.allready_taken_class_codes:
            self.allready_taken_class_codes.remove(class_code)
            self.something_changed = True

    def update_student_major(self, index):
        # Update the student's major in the based on the selected index
        self.student_major_id = index
        self.something_changed = True

    def remove_class_slot(self, class_code_names):
        for class_code_name in class_code_names:
            self.selected_class_code_names_set.remove(class_code_name)
        self.something_changed = True

    def add_class_option(self, class_code_name):
        if not self._is_it_allowed():
            return False
        
        class_id = self.class_code_name_to_id_map.get(class_code_name)
        if class_id:
                if class_code_name not in self.selected_class_code_names_set:
                    # self.selected_class_code_names[current_row].append(class_code_name)
                    self.selected_class_code_names_set.add(class_code_name)
                    self.something_changed = True
                    return True
                else:
                    self.parent.show_warning(self.ERROR_CLASS_ALLREADY_EXIST)
        else:
            self.parent.show_warning(self.ERROR_DB_NOT_EXIST)
        return False

    def remove_class_option(self, class_code_name):
        self.selected_class_code_names_set.remove(class_code_name)
        self.something_changed = True

    def populate_model_with_added_classes(self):
        lst = [self.classes[class_id][0]+'-'+self.classes[class_id][1] for class_id in self.added_classes.values()]
        self.added_classes_model.setStringList(lst)
    
    def insert_to_added_classes_model(self, class_id):
        class_items = self.classes[class_id]
        index = self.added_classes.bisect_left(class_items[0])
        lst = self.added_classes_model.stringList()
        lst.insert(index, class_items[0] + '-' + class_items[1])
        self.added_classes_model.setStringList(lst)
    
    def remove_from_added_classes_model(self, class_id):
        class_code = self.classes[class_id][0]
        index = self.added_classes.bisect_left(class_code)
        lst = self.added_classes_model.stringList()
        lst.pop(index)
        self.added_classes_model.setStringList(lst)

    def debug_course(self, course):
        print('*' * 30)
        for i in range(len(course)):
            if i == 1:
                value = self.professors[course[i]]
            elif i == 2:
                value = f"{self.classes[course[i]][0]},  {self.classes[course[i]][1]}"
            else:
                value = course[i]
            print(value)
        print('*' * 30)

    def load_data(self):
        self._create_tables_if_not_exist()
        cursor = self.conn.cursor()

        cursor.execute("SELECT major_name FROM Majors")
        self.majors = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT professor_name FROM Professors")
        self.professors = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT class_code_name FROM Classes")
        self.prerequisite_class_codes_set = set()
        for row in cursor.fetchall():
            self.prerequisite_class_codes_set.add(row[0])


    def fetch_major_specific_data(self):
        if self.student_major_id == 0:
            return
        
        cursor = self.conn.cursor()

        cursor.execute("SELECT course_ids FROM Majors WHERE major_id = ?", (self.student_major_id,))
        major_row = cursor.fetchone()
        
        course_ids = [int(course_id) for course_id in major_row[0].split(',')]
        
        cursor.execute(f"SELECT * FROM Courses WHERE course_id IN ({','.join('?' for _ in course_ids)})", course_ids)
        courses = cursor.fetchall()
        self.courses = {}
        for course in courses:
            course_lst = list(course[1:])
            course_lst[3] = [tuple(int(item) for item in time_tuple.split(',')) for time_tuple in course[4].split('&')]
            self.courses[course[0]] = course_lst
        
        self.class_id_to_course_ids_map = {}
        for course in courses:
            self.class_id_to_course_ids_map.setdefault(course[3], []).append(course[0])
        class_ids = tuple(self.class_id_to_course_ids_map.keys())
        cursor.execute(f"SELECT * FROM Classes WHERE class_id IN ({','.join('?' for _ in class_ids)})", class_ids)
        self.classes = {}
        self.class_code_name_to_id_map = {}
        classes = cursor.fetchall()
        for c in classes:
            c_lst = list(c[1:])
            c_lst[2] = [] if c[3] == '' else [[or_item for or_item in or_group.split('|')] for or_group in c[3].split('&')]
            self.classes[c[0]] = c_lst
            self.class_code_name_to_id_map[c[1]] = c[0]
            # For example class_code = EHB, class_number = 335E
            class_code, class_number = c[1].split(' ')
            self.class_code_to_class_ids_map.setdefault(class_code, SortedDict())[class_number] = c[0]

#################################################################################################
#       PRIVATE FUNCTIONS                                                                       #
#################################################################################################

    def _is_it_allowed(self):
        if self.student_major_id == 0:
            self.parent.show_warning(self.ERROR_MAJOR_NOT_SELECTED)
            return False
        return True

    # def _prerequisites_ok(self):
    #     class_ids = [class_id for class_slot in self.selected_class_ids for class_id in class_slot]

    #     for class_id in class_ids:
    #         if not self.check_prerequisites_for_class(class_id):
    #             return False, class_id # returns false and the problematic class id
        
    #     return True, 0 # returns 0 as an invalid value for class id because no class is problematic

    # Resturns a new list that same time courses are excluded
    def _exclude_same_time_courses(self, old_list, course_id_to_same_time_course_ids_map):
        result_list = []

        while old_list != []:
            new_list = []
            reference_course_id = old_list[0]
            lst = [reference_course_id]
            course_id_to_same_time_course_ids_map[reference_course_id] = lst
            result_list.append(reference_course_id)
            for i in range(1, len(old_list)):
                if self._are_two_courses_same_time(reference_course_id, old_list[i]):
                    lst.append(old_list[i])
                else:
                    new_list.append(old_list[i])

            old_list = new_list
        
        return result_list

    def _are_two_courses_same_time(self, course_id_1, course_id_2):
        time_tuples_1 = self.courses[course_id_1][3]
        time_tuples_2 = self.courses[course_id_2][3]

        return time_tuples_1 == time_tuples_2


    def _calculate_results(self, courses):
        i = 0
        self.potential_result = [0] * len(courses)
        self.temp_results = []
        self._calculate_recursive(courses, i)

    def _calculate_recursive(self, courses, i):
        if i >= len(courses):
            if self._check_potential_result():
                self.temp_results.append(self.potential_result.copy())
            return
        
        for j in range(len(courses[i])):
            self.potential_result[i] = courses[i][j]
            self._calculate_recursive(courses, i + 1)

    def _check_potential_result(self):
        if self.potential_result and self._excluded_time_blocks_ok() and self._no_collision_between_courses():
            return True
        return False
        
    def _excluded_time_blocks_ok(self):
        # Holds (day, start_time, end_time) tuples. start_time & end_time in minutes
        time_list = [time_tuple for course_id in self.potential_result for time_tuple in self.courses[course_id][3]]
        return not any(self._time_collision_not_ok(excluded_time_tuple, time_tuple)\
                    for excluded_time_tuple in self.excluded_time_blocks\
                    for time_tuple in time_list)

    @staticmethod    
    def _time_collision_not_ok(time_tuple1, time_tuple2):
        if time_tuple1[0] == 0 or time_tuple2[0] == 0:
            return False
        if time_tuple1[0] == time_tuple2[0]\
            and ((time_tuple1[1] < time_tuple2[2] and time_tuple1[2] > time_tuple2[1])\
                or (time_tuple1[2] < time_tuple2[1] and time_tuple1[1] > time_tuple2[2])):
            return True
        return False
    
    def _collision_for_exclusion_time_blocks_ok(self, new_block_tuple):
        for block_tuple in self.excluded_time_blocks:
            if self._time_collision_not_ok(block_tuple, new_block_tuple):
                return False
        return True
    
    def _no_collision_between_courses(self):
        for i in range(len(self.potential_result)):
            for j in range(i + 1, len(self.potential_result)):
                if any(self._time_collision_not_ok(time_tuple1, time_tuple2)\
                    for time_tuple1 in self.courses[self.potential_result[i]][3]\
                    for time_tuple2 in self.courses[self.potential_result[j]][3]):
                    return False
        return True


    def check_prerequisites_for_class(self, class_id):
        prerequisites = self.classes[class_id][2]

        for or_class_codes in prerequisites:
            if not any(class_code in self.allready_taken_class_codes for class_code in or_class_codes):
                self.parent.show_warning(self.ERROR_PREREQS_NOT_SATISFIED(class_id=class_id))
                return False
        
        return True
    
    @staticmethod
    def _total_minutes_to_HHmm(total_minutes):
        hour = total_minutes // 60
        minutes = total_minutes % 60
        return f'{hour:02d}:{minutes:02d}'
    
    @staticmethod
    def _time_to_minutes(time):
        return time.hour() * 60 + time.minute()
    
    def _create_tables_if_not_exist(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            crn TEXT,
            professor_id INTEGER,
            class_id INTEGER,
            time_tuples TEXT,
            quota INTEGER,
            FOREIGN KEY(professor_id) REFERENCES Professors(professor_id),
            FOREIGN KEY(class_id) REFERENCES Classes(class_id)
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Classes (
            class_id INTEGER PRIMARY KEY,
            class_code_name TEXT,
            class_title TEXT,
            prerequisite_class_ids TEXT -- Store as a comma-separated string
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Majors (
            major_id INTEGER PRIMARY KEY,
            major_name TEXT,
            course_ids TEXT -- Store as a comma-separated string
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Professors (
            professor_id INTEGER PRIMARY KEY,
            professor_name TEXT
        )''')
        self.conn.commit()