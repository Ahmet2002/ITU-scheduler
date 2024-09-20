from bs4 import BeautifulSoup
import sqlite3, json, re, logging, requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time



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
        self.class_codes = []
        self.class_code_ids = []
        self.token = ''
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

        i = len(self.class_code_ids) + 1
        for class_code_id in self.class_code_ids:
            if self.cancelled:
                return self._reset_state_and_return(self.CANCELLED)

            post_response = requests.get("https://obs.itu.edu.tr/public/DersProgram/DersProgramSearch?" + 
            f"ProgramSeviyeTipiAnahtari=LS&dersBransKoduId={class_code_id}&__RequestVerificationToken={self.token}")
            if post_response.status_code != 200:
                print(f'Invalid Response, status code: {post_response.status_code}')
                return self._reset_state_and_return(self.ERROR)

            try:
                data = json.loads(post_response.text)['dersProgramList']

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

    def get_class_code_ids_and_token(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Runs Chrome in headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model

        driver = webdriver.Chrome(options=chrome_options)

        try:
            driver.get('https://obs.itu.edu.tr/public/DersProgram')

            education_level_dropdown = Select(driver.find_element(By.ID, 'programSeviyeTipiId'))
            education_level_dropdown.select_by_value('LS')  # 'LS' is the value for "Undergraduate"

            WebDriverWait(driver, 5).until(
                lambda d: len(d.find_elements(By.XPATH, f"//select[@id='dersBransKoduId']/option")) > 1
            )

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            course_code_dropdown = soup.find('select', {'id': 'dersBransKoduId'})
            self.class_code_ids = [option['value'] for option in course_code_dropdown.find_all('option') if option['value']]

            self.token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]

            driver.get(self.prerequisites_url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'derskodu'))
            )
            dropdown = driver.find_element(By.NAME, 'derskodu')  # or By.CSS_SELECTOR or By.XPATH
            select = Select(dropdown)
            options = select.options
            self.class_codes = [option.get_attribute('value') for option in options]
        except:
            raise
        finally:
            driver.quit()





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