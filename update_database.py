from bs4 import BeautifulSoup
import sqlite3, json, re, logging, requests
from PyQt5.QtCore import pyqtSignal



# onsart linki
# https://www.sis.itu.edu.tr/TR/ogrenci/lisans/ders-bilgileri/ders-bilgileri.php?subj=MAT&numb=103

class CourseScraper:
    def __init__(self, logger):
        self._config()
        self.conn = None
        self.logger = logger
        self.course_list = []
        self.class_list = []
        self.professor_list = []
        self.majors_list = []
        self.professor_name_map = {}
        self.class_code_name_map = {}
        self.major_map = {}
        self.major_id_to_course_ids_map = {}
        self.class_iter = 1
        self.professor_iter = 1
        self.major_iter = 1
        self.cancelled = False

    def _config(self):
        self.max_class_day_count = 3
        self.prerequisites_url = 'https://www.sis.itu.edu.tr/TR/ogrenci/lisans/onsartlar/onsartlar.php'
        self.SUCCESS = 0
        self.ERROR = 1
        self.CANCELLED = 2
        self.days = {
            'Monday': 1,
            'Tuesday': 2,
            'Wednesday': 3,
            'Thursday': 4,
            'Friday': 5
        }
        self.class_codes = ['AKM', 'ATA', 'BED', 'BIL', 'BIO', 'BLG', 'BUS', 'CAB', 'CEV',
        'CHZ', 'CIE', 'CMP', 'COM', 'DEN', 'DFH', 'DNK', 'DUI', 'EAS', 'EEF', 'ECO',
        'ECN', 'EHB', 'EHN', 'EKO', 'ELE', 'ELH', 'ELK', 'END', 'ENR', 'ENT', 'ESL',
        'ETH', 'ETK', 'EUT', 'FIZ', 'GED', 'GEM', 'GEO', 'GID', 'GMI', 'GSB', 'GUV',
        'HUK', 'HSS', 'ICM', 'ILT', 'IML', 'ING', 'INS', 'ISE', 'ISL', 'ISH', 'ITB',
        'JDF', 'JEF', 'JEO', 'KIM', 'KMM', 'KMP', 'KON', 'MAD', 'MAK', 'MAL', 'MAR',
        'MAT', 'MCH', 'MEK', 'MEN', 'MET', 'MDN', 'MIM', 'MMD', 'MOD', 'MRT', 'MRE',
        'MRT', 'MTO', 'MTH', 'MTM', 'MTR', 'MST', 'MUH', 'MUK', 'MUT', 'MUZ', 'NAE',
        'NTH', 'PAZ', 'PEM', 'PET', 'PHE', 'PHY', 'RES', 'SBP', 'SAO', 'SES', 'STA',
        'STI', 'TDW', 'TEB', 'TEK', 'TEL', 'TER', 'TES', 'THO', 'TUR', 'UCK', 'UZB',
        'VBA', 'YTO', 'YZV']
        # CLASS CODE IDS FOR POST REQUEST FOR SCRAPING INDIVIDUAL WEB PAGES
        # THEY MAY CHANGE IN THE FUTURE SO YOU MAY HAVE TO UPDATE THEM
        self.class_code_ids = ['42', '227', '305', '302', '43', '200', '149', '165', '38', '30', '3', '180', '155', '127',
        '304', '7', '169', '137', '81', '142', '245', '146', '208', '168', '243', '10', '163', '181', '44', '32',
        '141', '232', '154', '289', '294', '297', '182', '196', '241', '39', '59', '2', '1', '178', '15', '183', 
        '179', '207', '225', '140', '164', '110', '22', '28', '226', '175', '138', '11', '74', '4', '162', '46', 
        '176', '109', '53', '173', '31', '177', '111', '256', '41', '301', '63', '253', '112', '300', '33', '8', 
        '153', '231', '14', '228', '255', '50', '9', '19', '18', '202', '27', '6', '125', '58', '156', '16', '12', 
        '48', '148', '26', '160', '293', '47', '258', '5', '20', '184', '290', '150', '157', '158', '257', '143', '174', 
        '260', '23', '199', '29', '40', '126', '128', '259', '263', '161', '151', '64', '17', '262', '147', '203', '36', 
        '307', '237', '21', '288', '171', '124', '291', '193', '172', '37', '159', '261', '121', '13', '57', '49', '269', 
        '129', '65', '215', '170', '34', '25', '195', '24', '306', '198', '213', '221']

    def trigger_cancel(self):
        self.cancelled = True


    def fetch_classes(self, progress_signal):
        if self._table_exists('Classes'):
            self.logger.debug('Classes table already exists.')
            self._load_class_code_name_map()
        else:
            return self._download_classes_if_not_exist(progress_signal)
        return self.SUCCESS

    def update_database(self, progress_signal):
        self._reset_state()
        return_code = self.fetch_classes(progress_signal)
        if return_code != self.SUCCESS:
            return self._reset_state_and_return(return_code)

        # URL of the page containing the table
        session = requests.Session()
        response = session.get("https://obs.itu.edu.tr/public/DersProgram")
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the verification token from the hidden input field
        token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]

        i = len(self.class_code_ids) + 1
        for class_code_id in self.class_code_ids:
            if self.cancelled:
                return self._reset_state_and_return(self.CANCELLED)
            
            # form_data = {
            #     "ProgramSeviyeTipiAnahtari": "LS",  # Example: 'LS' for Lisans
            #     "dersBransKoduId": class_code_id,  # Example: '196' for EHB (Electronics Classes)
            #     "__RequestVerificationToken": token  # Include the token
            # }

            post_response = session.get("https://obs.itu.edu.tr/public/DersProgram/DersProgramSearch?" + 
            f"ProgramSeviyeTipiAnahtari=LS&dersBransKoduId={class_code_id}&__RequestVerificationToken={token}")
            if post_response.status_code != 200:
                print(f'Invalid Response, status code: {post_response.status_code}')
                return self._reset_state_and_return(self.ERROR)

            try:
                data = json.loads(post_response.text)['dersProgramList']

                # Iterate over each row in the data
                for row in data:
                    if not self._row_ok(row):
                        continue
                    
                    class_id = self.class_code_name_map.get(row['dersKodu'])
                    if class_id is None:
                        class_id = self._get_new_class_id(row['dersKodu'], row['dersAdi'])
                    professor_id = self._get_professor_id(row['adSoyad'])
                    qouta = int(row['kontenjan']) - int(row['ogrenciSayisi'])
                    save = True
                    if qouta <= 0:
                        save = False

                    
                    if save:
                        time_tuples = self._parse_day_and_time(row['gunAdiEN'], row['baslangicSaati'])
                        # Append the data to a list
                        self.course_list.append([
                            row['crn'],
                            professor_id,
                            class_id,
                            time_tuples,
                            qouta
                        ])
                        
                    # COURSE_ID IS 1 INDEXED SO DONT SUBTRACT 1
                    self._save_major_and_course_ids(row['sinifProgram'], course_id=len(self.course_list), save=save) # returns major ids as a string not as a list
            except Exception:
                return self._reset_state_and_return(self.ERROR)
            
            progress_signal.emit(i)
            i += 1

        self.store_in_db()
        return self._reset_state_and_return(self.SUCCESS)
        

    def debug_course(self, course):
        print('*' * 30)
        for i, item in enumerate(course):
            if i == 2:
                item = self.professor_list[item - 1][1]
            elif i == 3:
                item = f"{self.class_list[item - 1][1]},  {self.class_list[item - 1][2]}"
            print(item)
        print('*' * 30)

    def debug_courses(self):
        for course in self.course_list:
            self.debug_course(course)

    def debug_classes(self):
        for c in self.class_list:
            print('*' * 30)
            for item in c:
                print(item)
            print('*' * 30)

    def debug_majors(self):
        for major in self.majors_list:
            print('*' * 30)
            for item in major:
                print(item)
            print('*' * 30)
##############################################################################################################################
# PRIVATE FUNCTIONS
##############################################################################################################################
    def _row_ok(self, row):
        if row['gunAdiEN'][0] == '-'\
        or row['baslangicSaati'][0] == '-':
            return False
        return True
    
    def _reset_state(self):
        self.course_list = []
        self.class_list = []
        self.professor_list = []
        self.majors_list = []
        self.professor_name_map = {}
        self.class_code_name_map = {}
        self.class_code_name_set = set()
        self.major_map = {}
        self.major_id_to_course_ids_map = {}
        self.class_iter = 1
        self.professor_iter = 1
        self.major_iter = 1
        self.cancelled = False

    def _reset_state_and_return(self, return_id):
        self._reset_state()
        return return_id

    def _get_professor_id(self, instructor):
        if instructor not in self.professor_name_map:
            self.professor_name_map[instructor] = self.professor_iter
            self.professor_list.append([
                self.professor_iter,
                instructor
            ])
            self.professor_iter += 1

        return self.professor_name_map[instructor]

    def _get_new_class_id(self, class_code, class_title):
        self.class_code_name_map[class_code] = self.class_iter
        self.class_list.append([
            self.class_iter,
            class_code,
            class_title,
            ''
        ])
        ret = self.class_iter
        self.class_iter += 1
        return ret

    def _save_major_and_course_ids(self, major_restriction, course_id, save=True):
        majors = [major.strip() for major in major_restriction.split(',')]

        for major in majors:
            if major not in self.major_map:
                self.major_map[major] = self.major_iter
                self.majors_list.append([
                    self.major_iter,
                    major,
                    ''
                ])
                self.major_iter += 1
        
        if save:
            for major in majors:
                self.major_id_to_course_ids_map.setdefault(self.major_map[major], []).append(course_id)

    def _parse_prerequisite_class_code_names(self, prerequisites):
        check = re.search(r'\s+ve\s*', prerequisites)
        if check is None:
            return []
        parsed_prereqs = [[re.search(r'\w+\s*\d+[A-Z]*', or_item).group() for or_item in re.split(r'\s*veya\s+', or_group)]
                        for or_group in re.split(r'\s*ve\s+', prerequisites)]
        return parsed_prereqs

    def _parse_day_and_time(self, day_str, time_str):
        days = [day.strip() for day in day_str.split(' ') if day.strip()]
        times = [time.strip() for time in time_str.split(' ') if time.strip()]

        day_values = [self.days.get(day, 0) for day in days] + [0] * (self.max_class_day_count - len(days))
        time_values = [
            (int(t[:2]) * 60 + int(t[3:])) for time in times for t in time.split('/')
        ] + [0] * (2 * self.max_class_day_count - len(times) * 2)
        time_tuples = []
        for i in range(len(day_values)):
            time_tuples.append((day_values[i], time_values[2 * i], time_values[2 * i + 1]))
        return '&'.join(','.join(str(time_item) for time_item in time_tuple) for time_tuple in time_tuples)
    
    def _table_exists(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?;
        """, (table_name,))
        return cursor.fetchone() is not None
    
    def _load_class_code_name_map(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT class_id, class_code_name FROM Classes")
        class_infos = cursor.fetchall()
        self.class_code_name_map = {row[1]: row[0] for row in class_infos}
        self.class_iter = len(class_infos) + 1

    
    def _download_classes_if_not_exist(self, progress_signal):

        class_list = []
        self.class_iter = 1

        i = 1
        for class_code in self.class_codes:
            if self.cancelled:
                return self.CANCELLED
            
            form_data = {'derskodu': class_code}
            response = requests.post(self.prerequisites_url, data=form_data)

            if response.status_code != 200:
                print(f'Invalid Response for prerequisites for {class_code}, status code: {response.status_code}')
                return self.ERROR

            try:
                soup = BeautifulSoup(response.content, 'html.parser')

                table = soup.find('table')
                if table is None:
                    continue

                for row in table.find_all('tr'):
                    columns = row.find_all('td')
                    if columns == []:
                        continue

                    not_parsed_prerequisites = columns[2].get_text(separator=' ')
                    parsed_prerequisites = self._parse_prerequisite_class_code_names(not_parsed_prerequisites)
                    class_list.append([
                        self.class_iter,
                        columns[0].text.strip(),
                        columns[1].text.strip(),
                        '&'.join('|'.join(or_group) for or_group in parsed_prerequisites)
                    ])
                    self.class_iter += 1
            except Exception:
                return self.ERROR
            
            progress_signal.emit(i)
            i += 1

        self.class_code_name_map = {c[1]: c[0] for c in class_list}
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Classes (
            class_id INTEGER PRIMARY KEY,
            class_code_name TEXT,
            class_title TEXT,
            prerequisite_class_ids TEXT -- Store as a comma-separated string
        )
        ''')
        self.conn.commit()
        cursor.executemany('''INSERT INTO Classes (class_id, class_code_name, class_title, prerequisite_class_ids)
                                VALUES (?, ?, ?, ?)''', class_list)
        self.conn.commit()
        return self.SUCCESS
    
    def store_in_db(self):
        self._create_tables_if_not_exist()
        cursor = self.conn.cursor()

        for table in ['Courses', 'Professors', 'Majors']:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='Courses'")
        self.conn.commit()

        cursor.executemany('''INSERT INTO Courses (crn, professor_id, class_id, time_tuples, quota) 
                            VALUES (?, ?, ?, ?, ?)''', self.course_list)
        self.conn.commit()

        cursor.executemany('''INSERT INTO Classes (class_id, class_code_name, class_title, prerequisite_class_ids)
                            VALUES (?, ?, ?, ?)''', self.class_list)
        self.conn.commit()

        cursor.executemany('''INSERT INTO Professors (professor_id, professor_name)
                            VALUES (?, ?)''', self.professor_list)
        self.conn.commit()

        # Starts from 1 goes to len of self.majors_list 
        # for major_id in range(1, len(self.majors_list) + 1):
        #     self.majors_list[major_id - 1].append(','.join(str(course_id_int) for course_id_int in self.major_id_to_course_ids_map.get(major_id, [])))

        for key, value in self.major_id_to_course_ids_map.items():
            self.majors_list[key - 1][2] = ','.join(str(course_id_int) for course_id_int in value)

        cursor.executemany('''INSERT INTO Majors (major_id, major_name, course_ids)
                            VALUES (?, ?, ?)''', self.majors_list)
        self.conn.commit()

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



if __name__ == '__main__':
    class DummyClass:
        def emit(self, num):
            pass

    logger = logging.getLogger()
    dummy_object = DummyClass()  # Signal to update progress bar
    scraper = CourseScraper(logger)
    scraper.conn = sqlite3.connect('courses.db')
    return_code = scraper.update_database(dummy_object)
    scraper.conn.close()
    print(f'return code: {return_code}')

#     # BEFORE DEBUGGING
#     # CHECK IF _reset_state_and_return IN THE LAST PART OF UPDATE_DATA_BASE()
#     # IS COMMENTED OUT OR NOT IT SHOULD BE COMMENTED OUT
#     # IF NOTHING SHOWS UP IN THE TERMINAL
#     # scraper.debug_courses()
#     scraper.debug_classes()
#     # scraper.debug_majors()