from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
import sqlite3


class LoginPage(Screen):
    error = None
    username = ObjectProperty(None)
    password = ObjectProperty(None)

    def login(self):
        if self.username.text != "" and self.password.text != "":
            if self.username.text == "admin" and self.password.text == "admin":
                self.manager.current = 'Menu Page'
            else:
                self.incorrect_popup()

        self.username.text = ""
        self.password.text = ""

    def incorrect_popup(self):
        self.error = MDDialog(
            text="Incorrect Username or Password!!! Please fill in the fields again",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=self.close_dialog_box
                )
            ]
        )
        self.error.open()

    # Click Ok Button
    def close_dialog_box(self, obj):
        self.error.dismiss()


class MenuPage(Screen):
    def __init__(self, **kwargs):
        super(MenuPage, self).__init__(**kwargs)
        self.appointment_list = []
        self.show_appointment = None
        self.appointment_delete = None
        self.appointment_row_data = None

    def go_to_schedule_page(self):
        self.manager.current = "Schedule Page"
        self.manager.transition.direction = "left"

    def fetching_appointment_data(self):
        self.appointment_list.clear()
        # FETCH DATA FROM DATABASE FOR THE  MDDATATABLE
        conn = sqlite3.connect('patient_records.db')
        c = conn.cursor()
        c.execute("SELECT name, mobile_number, schedule, date, time FROM records ORDER BY date ASC, time ASC")
        rows = c.fetchall()
        for each_row in rows:
            if all(value is not None for value in each_row):
                self.appointment_list.append(list(each_row))
        conn.commit()
        conn.close()

    def update_appointment(self):
        # UPDATING THE DATATABLE IN MENUP AGE
        self.fetching_appointment_data()
        show_appointment = MDDataTable(
            pos_hint={"center_x": 0.25, "center_y": 0.43},
            size_hint=(0.48, 0.6),
            column_data=[
                ("NAME", dp(35)),
                ("CONTACT", dp(35)),
                ("APPOINTMENT", dp(35)),
                ("DATE", dp(35)),
                ("TIME", dp(35)),
            ],
            row_data=self.appointment_list

        )
        self.add_widget(show_appointment)

    def on_enter(self, *args):
        self.update_appointment()

    # SHOWING CHECKBOX FOR DELETION
    def appointment_deletion_checkbox(self):
        if self.show_appointment is not None:
            self.remove_widget(self.show_appointment)
        show_appointment = MDDataTable(
            pos_hint={"center_x": 0.25, "center_y": 0.43},
            size_hint=(0.48, 0.6),
            column_data=[
                ("NAME", dp(35)),
                ("CONTACT", dp(35)),
                ("APPOINTMENT", dp(35)),
                ("DATE", dp(35)),
                ("TIME", dp(35)),
            ],
            row_data=self.appointment_list,
            check=True
        )
        if show_appointment is not None:
            show_appointment.bind(on_check_press=self.delete_row)
        self.add_widget(show_appointment)

    # SHOWING DELETION DIALOG BOX
    def delete_row(self, instance_show_records, current_row):
        self.appointment_delete = MDDialog(
            text="Are you sure you want to cancel this appointment? ",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=self.close_deletion_alert_box
                ),
                MDFlatButton(
                    text="PROCEED",
                    on_release=self.proceed_with_deletion
                )
            ]
        )
        self.appointment_row_data = current_row
        self.appointment_delete.open()

    def close_deletion_alert_box(self, obj):
        self.appointment_delete.dismiss()
        self.update_appointment()

    def proceed_with_deletion(self, obj):
        if self.appointment_row_data is not None:
            reference = (str(self.appointment_row_data[1]))
            try:
                conn = sqlite3.connect('patient_records.db')
                c = conn.cursor()
                c.execute("UPDATE records SET schedule=NULL, date=NULL, time=NULL WHERE mobile_number=?",
                          (reference,)
                          )

                conn.commit()
                conn.close()
                self.appointment_delete.dismiss()
                self.update_appointment()

            except Exception as e:
                print(e)


class SchedulePage(Screen):
    def __init__(self, **kwargs):
        super(SchedulePage, self).__init__(**kwargs)
        self.schedule_dropdown = None
        self.schedule_menu = None
        self.error_box = None

    # SCHEDULING AN APPOINTMENT/OT

    def show_schedule(self):
        self.schedule_menu = [
            {
                "viewclass": "OneLineListItem",
                "text": "Consultation",
                "on_release": lambda x="Consultation": self.schedule_input(x)
            },
            {
                "viewclass": "OneLineListItem",
                "text": "OT",
                "on_release": lambda x="OT": self.schedule_input(x)
            }
        ]
        self.schedule_dropdown = MDDropdownMenu(
            caller=self.ids.schedule,
            items=self.schedule_menu,
            width_mult=4
        )
        self.schedule_dropdown.open()

    def schedule_input(self, value):
        self.ids.schedule.text = value

    # CREATING A CALENDAR

    def date_save(self, instance, value, date_range):
        self.ids.date.text = str(value)

    def show_date(self):
        calendar = MDDatePicker()
        calendar.bind(on_save=self.date_save)
        calendar.open()

        # ALLOCATING THE TIME

    def time_save(self, instance, time):
        self.ids.time.text = str(time)

    def show_time(self):
        clock = MDTimePicker()
        clock.bind(time=self.time_save)
        clock.open()

    # DATA VALIDATION
    def validate(self):
        schedule = self.ids.schedule.text.strip()
        date = self.ids.date.text.strip()
        time = self.ids.time.text.strip()

        if schedule == "" or date == "" or time == "":
            self.show_error_box(" Please fill in the necessary fields")
            return False

        return True

    # CREATING ERROR MESSAGE FOR DATA VALIDATION
    def show_error_box(self, message):
        self.error_box = MDDialog(
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=self.close_error_box
                )
            ]
        )
        self.error_box.open()

    def close_error_box(self, obj):
        self.error_box.dismiss()

    # CREATING THE SCHEDULE BUTTON

    def create_schedule(self):
        reference_mobile_appointment = str(self.ids.mobile_appointment.text)
        set_schedule = self.ids.schedule.text
        set_date = self.ids.date.text
        set_time = self.ids.time.text
        if not self.validate():
            return

        try:
            conn = sqlite3.connect('patient_records.db')
            c = conn.cursor()
            c.execute("UPDATE records SET schedule=?, date=?, time=? WHERE mobile_number=?",
                      (set_schedule, set_date, set_time, reference_mobile_appointment,)
                      )
            conn.commit()
            conn.close()

            # GO BACK TO MENU PAGE
            self.manager.current = "Menu Page"
            self.manager.transition.direction = "right"
        except ValueError:
            self.show_error_box("Could not find patient. Please try again")

    def clear(self):
        self.ids.name_appointment.text = ""
        self.ids.mobile_appointment.text = ""
        self.ids.schedule.text = ""
        self.ids.date.text = ""
        self.ids.time.text = ""


class AddRecords(Screen):
    success = None
    # CREATING THE DATABASE
    conn = sqlite3.connect('patient_records.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE if not exists records( name text, age integer, gender text, mobile_number integer,
     meds text,status text,schedule text,date text, time text)""")
    conn.commit()
    conn.close()

    def __init__(self, **kwargs):
        super(AddRecords, self).__init__(**kwargs)
        self.gender_menu = None
        self.gender_dropdown = None
        self.status_menu = None
        self.status_dropdown = None
        self.error_msg = None

    # ## DROPDOWN BOXES ## #

    # GENDER
    def show_gender_dropdown(self):
        self.gender_menu = [
            {
                "viewclass": "OneLineListItem",
                "text": "Male",
                "on_release": lambda x="Male": self.gender_input(x)
            },
            {
                "viewclass": "OneLineListItem",
                "text": "Female",
                "on_release": lambda x="Female": self.gender_input(x)
            }
        ]
        self.gender_dropdown = MDDropdownMenu(
            caller=self.ids.gender,
            items=self.gender_menu,
            width_mult=4
        )
        self.gender_dropdown.open()

    def gender_input(self, value):
        self.ids.gender.text = value

    # STATUS

    def show_status_dropdown(self):
        self.status_menu = [
            {
                "viewclass": "OneLineListItem",
                "text": "Ongoing",
                "on_release": lambda x="Ongoing": self.status_input(x)
            },
            {
                "viewclass": "OneLineListItem",
                "text": "Discharged",
                "on_release": lambda x="Discharged": self.status_input(x)
            }
        ]
        self.status_dropdown = MDDropdownMenu(
            caller=self.ids.status,
            items=self.status_menu,
            width_mult=4
        )
        self.status_dropdown.open()

    def status_input(self, value):
        self.ids.status.text = value

    # DATA VALIDATION
    def validate(self):
        name = self.ids.name.text.strip()
        age = self.ids.age.text.strip()
        gender = self.ids.gender.text.strip()
        mobile = self.ids.mobile.text.strip()
        meds = self.ids.meds.text.strip()
        status = self.ids.status.text.strip()

        if name == "" or age == "" or gender == "" or mobile == "" or status == "":
            self.show_error_msg(" Please fill in the necessary fields")
            return False
        try:
            age = int(age)
        except ValueError:
            self.show_error_msg(" Age must be an integer")
            return False
        try:
            mobile = int(mobile)
        except ValueError:
            self.show_error_msg("Mobile Number must be an integer")
            return False
        try:
            name = str(name)
        except ValueError:
            self.show_error_msg(" Please enter a valid name")
            return False
        try:
            meds = str(meds)
        except ValueError:
            self.show_error_msg(" Please enter a valid name")
            return False

        return True

    # CREATING ERROR MESSAGE FOR DATA VALIDATION
    def show_error_msg(self, message):
        self.error_msg = MDDialog(
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=self.close_error_msg
                )
            ]
        )
        self.error_msg.open()

    def close_error_msg(self, obj):
        self.error_msg.dismiss()

    # CREATING THE SUBMIT BUTTON FOR THE RECORDS
    def submit(self):
        if not self.validate():
            return

        conn = sqlite3.connect('patient_records.db')
        c = conn.cursor()
        c.execute("INSERT INTO records(name, age, gender, mobile_number, meds, status) VALUES("
                  ":name, "
                  ":age, :gender, :phone, :meds, :status)",
                  {
                      'name': self.ids.name.text,
                      'age': self.ids.age.text,
                      'gender': self.ids.gender.text,
                      'phone': self.ids.mobile.text,
                      'meds': self.ids.meds.text,
                      'status': self.ids.status.text
                  })
        conn.commit()
        self.show_success_msg("Data Inserted Successfully!!!")
        self.clear()
        conn.close()

    # SUCCESS DIALOG BOX
    def show_success_msg(self, message):
        self.success = MDDialog(
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=self.close_dialog_box
                )
            ]
        )
        self.success.open()

    # CLICK OK BUTTON
    def close_dialog_box(self, obj):
        self.success.dismiss()

    # CLEAR RECORDS
    def clear(self):
        self.ids.name.text = ""
        self.ids.age.text = ""
        self.ids.gender.text = ""
        self.ids.mobile.text = ""
        self.ids.meds.text = ""
        self.ids.status.text = ""


class ViewRecords(Screen):
    def __init__(self, **kwargs):
        super(ViewRecords, self).__init__(**kwargs)
        self.show_records = None
        self.deletion_proceed = None
        self.current_row_data = None
        self.records_results = []

    def fetching_data(self):
        self.records_results.clear()
        # FETCH DATA FROM DATABASE FOR THE  MDDATATABLE

        conn = sqlite3.connect('patient_records.db')
        c = conn.cursor()
        c.execute("SELECT name, age, gender, mobile_number, meds, status FROM records ORDER BY status DESC, name ASC")
        rows = c.fetchall()
        for each_row in rows:
            self.records_results.append(list(each_row))
        conn.commit()
        conn.close()

    def show_datatable(self):
        self.fetching_data()
        # CREATING DATATABLE
        show_records = MDDataTable(
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint=(0.8, 0.7),
            use_pagination=True,
            rows_num=20,
            column_data=[
                ("NAME", dp(30)),
                ("AGE", dp(30)),
                ("GENDER", dp(30)),
                ("NUMBER", dp(30)),
                ("MEDICATION", dp(30)),
                ("STATUS", dp(30))
            ],
            row_data=self.records_results

        )
        self.add_widget(show_records)
        if self.ids.cancel_button.opacity == 1:
            self.ids.cancel_button.opacity = 0

    def on_enter(self, *args):
        self.show_datatable()

    # SHOWING CHECKBOX FOR UPDATE
    def show_check_for_update(self):
        if self.show_records is not None:
            self.remove_widget(self.show_records)
        show_records = MDDataTable(
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint=(0.8, 0.7),
            use_pagination=True,
            rows_num=20,
            column_data=[
                ("NAME", dp(30)),
                ("AGE", dp(30)),
                ("GENDER", dp(30)),
                ("NUMBER", dp(30)),
                ("MEDICATION", dp(30)),
                ("STATUS", dp(30))
            ],
            row_data=self.records_results,
            check=True

        )
        if show_records is not None:
            show_records.bind(on_check_press=self.update_row)
        self.add_widget(show_records)
        if self.ids.cancel_button.opacity == 0:
            self.ids.cancel_button.opacity = 1

    def update_row(self, instance_show_records, current_row):
        self.manager.current = 'Update Records'
        self.current_row_data = current_row
        self.manager.ids.update_records.ids.name_update.text = self.current_row_data[0]
        self.manager.ids.update_records.ids.age_update.text = self.current_row_data[1]
        self.manager.ids.update_records.ids.gender_update.text = self.current_row_data[2]
        self.manager.ids.update_records.ids.mobile_update.text = self.current_row_data[3]
        self.manager.ids.update_records.ids.meds_update.text = self.current_row_data[4]
        self.manager.ids.update_records.ids.status_update.text = self.current_row_data[5]

    # SHOWING CHECKBOX FOR DELETION
    def show_check_for_deletion(self):
        if self.show_records is not None:
            self.remove_widget(self.show_records)
        show_records = MDDataTable(
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint=(0.8, 0.7),
            use_pagination=True,
            rows_num=20,
            column_data=[
                ("NAME", dp(30)),
                ("AGE", dp(30)),
                ("GENDER", dp(30)),
                ("NUMBER", dp(30)),
                ("MEDICATION", dp(30)),
                ("STATUS", dp(30))
            ],
            row_data=self.records_results,
            check=True

        )
        if show_records is not None:
            show_records.bind(on_check_press=self.delete_row)
        self.add_widget(show_records)

        if self.ids.cancel_button.opacity == 0:
            self.ids.cancel_button.opacity = 1

    def delete_row(self, instance_show_records, current_row):
        self.deletion_proceed = MDDialog(
            text="Are you sure you want to delete this record?",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=self.close_deletion_alert_box
                ),
                MDFlatButton(
                    text="PROCEED",
                    on_release=self.proceed_with_deletion
                )
            ]
        )
        self.current_row_data = current_row
        self.deletion_proceed.open()

    def close_deletion_alert_box(self, obj):
        self.deletion_proceed.dismiss()

    def proceed_with_deletion(self, obj):
        if self.current_row_data is not None:
            reference_mobile = (str(self.current_row_data[3]))
            try:
                conn = sqlite3.connect('patient_records.db')
                c = conn.cursor()
                c.execute("DELETE FROM records WHERE mobile_number=?", (reference_mobile,))

                conn.commit()
                conn.close()
                self.deletion_proceed.dismiss()
                self.show_datatable()

            except Exception as e:
                print(e)


class UpdateRecords(Screen):
    def __init__(self, **kwargs):
        super(UpdateRecords, self).__init__(**kwargs)
        self.gender_menu_update = None
        self.gender_dropdown_update = None
        self.status_menu_update = None
        self.status_dropdown_update = None

    def show_gender_dropdown_for_update(self):
        self.gender_menu_update = [
            {
                "viewclass": "OneLineListItem",
                "text": "Male",
                "on_release": lambda x="Male": self.gender_update(x)
            },
            {
                "viewclass": "OneLineListItem",
                "text": "Female",
                "on_release": lambda x="Female": self.gender_update(x)
            }
        ]
        self.gender_dropdown_update = MDDropdownMenu(
            caller=self.ids.gender_update,
            items=self.gender_menu_update,
            width_mult=4
        )
        self.gender_dropdown_update.open()

    def gender_update(self, value):
        self.ids.gender_update.text = value

    def show_status_dropdown_for_update(self):
        self.status_menu_update = [
            {
                "viewclass": "OneLineListItem",
                "text": "Ongoing",
                "on_release": lambda x="Ongoing": self.status_update(x)
            },
            {
                "viewclass": "OneLineListItem",
                "text": "Discharged",
                "on_release": lambda x="Discharged": self.status_update(x)
            }
        ]
        self.status_dropdown_update = MDDropdownMenu(
            caller=self.ids.status_update,
            items=self.status_menu_update,
            width_mult=4
        )
        self.status_dropdown_update.open()

    def status_update(self, value):
        self.ids.status_update.text = value

    def update(self):
        # EXTRACTING UPDATED DATA
        new_name = self.ids.name_update.text
        new_age = self.ids.age_update.text
        new_gender = self.ids.gender_update.text
        new_mobile = self.ids.mobile_update.text
        new_meds = self.ids.meds_update.text
        new_status = self.ids.status_update.text

        # UPDATING THE DATABASE

        try:
            conn = sqlite3.connect('patient_records.db')
            c = conn.cursor()
            c.execute(
                "UPDATE records SET name=?, age=?, gender=?, meds=?, status=? WHERE ""mobile_number=?",
                (new_name, new_age, new_gender, new_meds, new_status, new_mobile,))
            conn.commit()
            conn.close()
            self.manager.current = 'View Records'
        except Exception as e:
            print(e)


class Manager(ScreenManager):
    pass


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        return


MainApp().run()
