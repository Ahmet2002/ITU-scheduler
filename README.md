# ITU Scheduler

This program is designed to help students schedule their classes by parsing course data, displaying available options, and allowing users to manage their schedules easily. The application has a graphical interface built using `PyQt5` and uses web scraping to gather the course information from the university's website. Additionally, it provides options to export schedules, navigate between different scheduling results, and update the course database.

## Features

- **Class Selection:** Allows users to choose classes from the available course list.
- **Auto-Suggestion:** Provides an autocomplete feature to make class selection faster.
- **Timetable Display:** Visualizes your selected classes on a timetable.
- **Time Exclusion Blocks:** You can block out certain times of the day to avoid scheduling classes during those periods.
- **Schedule Navigation:** Easily navigate between different possible combinations of schedules.
- **Generate Combinations:** Automatically generate all possible schedule combinations based on the selected classes.
- **Exporting:** Export your final schedule in PDF or image format.
- **Database Update:** Automatically fetches the latest course information from the university's website.

## Usage

1. **Select Classes:** Navigate to the "Select Classes" tab, where you can enter class names with the help of the auto-suggestion feature.
2. **View Timetable:** Once you have selected your classes, the timetable will be displayed, showing the schedule for each selected course.
3. **Add Time Exclusion Blocks:** You can block specific time periods by using the "Add/Remove Time Exclusion Blocks" feature to ensure no classes are scheduled during those times.
4. **Generate Combinations:** Based on your selections, the scheduler will generate all possible class combinations for you to choose from.
5. **Navigation:** You can switch between different schedule options using the "Next" and "Previous" buttons.
6. **Export Schedule:** After finalizing your schedule, you can export it in PDF or image format by clicking the "Export" button.
7. **Update Database:** To get the latest course data, click the "Update Database" button, which will scrape the necessary information from the university's website.


## Prerequisites

Before running the program, make sure you have Python installed. You will also need to install the required dependencies.

## Installation

1. Clone this repository to your local machine:

    ```bash
    git clone https://github.com/Ahmet2002/ITU-scheduler.git
    ```

2. Navigate to the project directory:

    ```bash
    cd ITU-scheduler
    ```

3. Install the required packages by running:

    ```bash
    pip install -r requirements.txt
    ```

## Running the Program

Once the dependencies are installed, you can run the program using the following command:

```bash
python main.py
