# gui.py
import sys
import os
from datetime import datetime

import cv2

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QMessageBox, QSpinBox, QGroupBox,
    QFormLayout, QFileDialog, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QComboBox
)
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer

from db import (
    init_db, save_result, fetch_results,
    fetch_students, add_student, update_student, delete_student,
    clear_all_results,
)
from omr_core import process_omr, detect_answer_key, get_debug_stack
import analytics


# ===================== Dialog: إدارة الطلاب =====================
class StudentsDialog(QDialog):
    """
    إدارة الطلاب:
    - عرض قائمة الطلاب
    - إضافة / تعديل / حذف
    - استيراد من Excel (id + name)
    - عرض صورة ورقة الطالب (إن وجدت)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("👨‍🎓 Manage Students")
        self.resize(800, 520)

        self.selected_id = None

        layout = QVBoxLayout(self)

        # جدول الطلاب
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["DB ID", "Student ID", "Student Name", "Created At"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellClicked.connect(self.on_row_selected)
        layout.addWidget(self.table)

        # حقول الإدخال
        form_layout = QFormLayout()
        self.student_id_edit = QLineEdit()
        self.student_name_edit = QLineEdit()
        form_layout.addRow("Student ID:", self.student_id_edit)
        form_layout.addRow("Student Name:", self.student_name_edit)
        layout.addLayout(form_layout)

        # أزرار
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.clicked.connect(self.add_student)

        self.update_btn = QPushButton("✏️ Update")
        self.update_btn.clicked.connect(self.update_student)

        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.clicked.connect(self.delete_student)

        self.import_btn = QPushButton("📥 Import from Excel")
        self.import_btn.clicked.connect(self.import_from_excel)

        self.show_img_btn = QPushButton("🖼 Show Sheet Image")
        self.show_img_btn.clicked.connect(self.show_student_image)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.show_img_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.load_students()

    def load_students(self):
        rows = fetch_students()
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            db_id, sid, sname, created_at = row
            self.table.setItem(r, 0, QTableWidgetItem(str(db_id)))
            self.table.setItem(r, 1, QTableWidgetItem(str(sid)))
            self.table.setItem(r, 2, QTableWidgetItem(str(sname)))
            self.table.setItem(r, 3, QTableWidgetItem(str(created_at)))
        self.selected_id = None
        self.student_id_edit.clear()
        self.student_name_edit.clear()

    def on_row_selected(self, row, col):
        db_id_item = self.table.item(row, 0)
        sid_item = self.table.item(row, 1)
        sname_item = self.table.item(row, 2)

        self.selected_id = int(db_id_item.text()) if db_id_item else None
        sid = sid_item.text() if sid_item else ""
        sname = sname_item.text() if sname_item else ""

        self.student_id_edit.setText(sid)
        self.student_name_edit.setText(sname)

        parent = self.parent()
        if parent is not None:
            try:
                parent.student_id_edit.setText(sid)
                parent.student_name_edit.setText(sname)
                parent.load_students_to_combo()
            except AttributeError:
                pass

    def add_student(self):
        sid = self.student_id_edit.text().strip()
        sname = self.student_name_edit.text().strip()
        if not sid or not sname:
            QMessageBox.warning(self, "Warning", "Please enter student ID and name.")
            return
        try:
            add_student(sid, sname)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        self.load_students()

    def update_student(self):
        if self.selected_id is None:
            QMessageBox.warning(self, "Warning", "Select a student first.")
            return
        sid = self.student_id_edit.text().strip()
        sname = self.student_name_edit.text().strip()
        if not sid or not sname:
            QMessageBox.warning(self, "Warning", "Please enter student ID and name.")
            return
        try:
            update_student(self.selected_id, sid, sname)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        self.load_students()

    def delete_student(self):
        if self.selected_id is None:
            QMessageBox.warning(self, "Warning", "Select a student to delete.")
            return
        if QMessageBox.question(
            self, "Confirm", "Delete this student?", QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.No:
            return
        delete_student(self.selected_id)
        self.load_students()

    def import_from_excel(self):
        """
        استيراد طلاب من ملف Excel يحتوي عمودين:
        id , name (أو student_id , student_name)
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel file", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            import pandas as pd
        except ImportError:
            QMessageBox.critical(
                self,
                "Error",
                "pandas/openpyxl are required.\nInstall with:\n\npip install pandas openpyxl",
            )
            return

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read Excel file:\n{e}")
            return

        if df.empty:
            QMessageBox.warning(self, "Warning", "Excel file is empty.")
            return

        cols_lower = [str(c).strip().lower() for c in df.columns]
        id_col = None
        name_col = None
        for i, c in enumerate(cols_lower):
            if c in ("id", "student_id", "no", "number"):
                id_col = df.columns[i]
            if c in ("name", "student_name", "full_name"):
                name_col = df.columns[i]

        if id_col is None or name_col is None:
            QMessageBox.warning(
                self,
                "Warning",
                "Excel must contain columns for id and name\n(e.g. id, name).",
            )
            return

        count_ok = count_dup = count_skip = count_err = 0

        for _, row in df.iterrows():
            sid = str(row[id_col]).strip() if row[id_col] is not None else ""
            sname = str(row[name_col]).strip() if row[name_col] is not None else ""

            if not sid or sid.lower() == "nan" or not sname or sname.lower() == "nan":
                count_skip += 1
                continue

            try:
                add_student(sid, sname)
                count_ok += 1
            except ValueError:
                count_dup += 1
            except Exception:
                count_err += 1

        self.load_students()
        parent = self.parent()
        if parent is not None:
            try:
                parent.load_students_to_combo()
            except AttributeError:
                pass

        QMessageBox.information(
            self,
            "Import finished",
            f"Imported: {count_ok}\n"
            f"Duplicates: {count_dup}\n"
            f"Empty rows: {count_skip}\n"
            f"Errors: {count_err}",
        )

    def show_student_image(self):
        """
        عرض آخر صورة محفوظة لورقة هذا الطالب (إن وجدت) من مجلد Results.
        """
        sid = self.student_id_edit.text().strip()
        if not sid:
            QMessageBox.warning(self, "Warning", "Select a student or fill Student ID.")
            return

        results_dir = "Results"
        if not os.path.isdir(results_dir):
            QMessageBox.information(self, "Info", "No Results folder yet.")
            return

        # نبحث عن جميع الملفات التي تبدأ برقم هذا الطالب
        candidates = []
        for fname in os.listdir(results_dir):
            if fname.startswith(f"{sid}_") and fname.lower().endswith(".png"):
                full_path = os.path.join(results_dir, fname)
                candidates.append(full_path)

        if not candidates:
            QMessageBox.information(
                self,
                "Info",
                f"No sheet image found for student ID: {sid}",
            )
            return

        # نأخذ أحدث ملف حسب وقت التعديل
        candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        latest_path = candidates[0]

        img = cv2.imread(latest_path)
        if img is None:
            QMessageBox.warning(self, "Warning", "Could not read image file.")
            return

        # عرض الصورة في Dialog بسيط
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Sheet Image - {sid}")
        dlg.resize(800, 600)

        v = QVBoxLayout(dlg)
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        v.addWidget(lbl)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        lbl.setPixmap(
            pix.scaled(
                780,
                540,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        v.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.exec()


# ===================== الواجهة الرئيسية =====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("📄 OMR Scanner – GUI + DB + Analytics")
        self.resize(1200, 750)

        self.current_score = None
        self.current_answers = None
        self.current_frame = None
        self.correct_answers = None
        self.last_result_img = None  # آخر صورة مصححة (لنحفظها عند حفظ النتيجة فقط)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera_frame)

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        # -------- العمود الأيسر --------
        left_layout = QVBoxLayout()

        # بيانات الطالب والاختبار
        form_box = QGroupBox("Student & Exam")
        form_layout = QFormLayout()

        self.student_combo = QComboBox()
        self.student_combo.currentIndexChanged.connect(self.on_student_combo_changed)

        self.student_id_edit = QLineEdit()
        self.student_id_edit.setPlaceholderText("e.g. 20251001")

        self.student_name_edit = QLineEdit()
        self.student_name_edit.setPlaceholderText("Student name")

        self.exam_code_edit = QLineEdit()
        self.exam_code_edit.setPlaceholderText("e.g. QUIZ1")

        form_layout.addRow("Select student:", self.student_combo)
        form_layout.addRow("Student ID:", self.student_id_edit)
        form_layout.addRow("Student Name:", self.student_name_edit)
        form_layout.addRow("Exam Code:", self.exam_code_edit)

        form_box.setLayout(form_layout)
        left_layout.addWidget(form_box)

        # إعدادات OMR
        settings_box = QGroupBox("OMR Settings")
        settings_layout = QFormLayout()

        self.questions_spin = QSpinBox()
        self.questions_spin.setRange(1, 100)
        self.questions_spin.setValue(10)

        self.choices_spin = QSpinBox()
        self.choices_spin.setRange(2, 10)
        self.choices_spin.setValue(4)

        self.ans_edit = QLineEdit()
        self.ans_edit.setPlaceholderText("e.g. 0,1,2,3,0,1,2,3,0,1")
        self.ans_edit.setText("0,1,2,3,0,1,2,3,0,1")

        settings_layout.addRow("Questions:", self.questions_spin)
        settings_layout.addRow("Choices per Q:", self.choices_spin)
        settings_layout.addRow("Correct answers:", self.ans_edit)

        settings_box.setLayout(settings_layout)
        left_layout.addWidget(settings_box)

        # أزرار التحكم
        buttons_box = QGroupBox("Controls")
        buttons_layout = QVBoxLayout()

        self.start_cam_btn = QPushButton("🎥 Start / Stop Camera")
        self.start_cam_btn.clicked.connect(self.toggle_camera)

        self.load_image_btn = QPushButton("📁 Load Sheet Image")
        self.load_image_btn.clicked.connect(self.load_image_from_file)

        self.scan_key_btn = QPushButton("📋 Scan Correct Answer Sheet (Key)")
        self.scan_key_btn.clicked.connect(self.scan_answer_key)

        self.capture_btn = QPushButton("📸 Capture & Grade Sheet")
        self.capture_btn.clicked.connect(self.capture_and_process)

        self.save_btn = QPushButton("💾 Save Result to DB (and image)")
        self.save_btn.clicked.connect(self.save_to_db)

        self.manage_students_btn = QPushButton("👨‍🎓 Manage Students")
        self.manage_students_btn.clicked.connect(self.open_students_dialog)

        self.show_log_btn = QPushButton("📜 Show Results Log")
        self.show_log_btn.clicked.connect(self.show_results_log)

        self.analytics_btn = QPushButton("📊 Show Score Analytics")
        self.analytics_btn.clicked.connect(self.show_analytics)

        self.export_excel_btn = QPushButton("📥 Export Results to Excel")
        self.export_excel_btn.clicked.connect(self.export_results_excel)

        self.clear_results_btn = QPushButton("🧹 Clear All Results")
        self.clear_results_btn.clicked.connect(self.clear_all_results_dialog)

        self.show_steps_btn = QPushButton("🔍 Show OMR Steps (Debug)")
        self.show_steps_btn.clicked.connect(self.show_omr_steps)

        buttons_layout.addWidget(self.start_cam_btn)
        buttons_layout.addWidget(self.load_image_btn)
        buttons_layout.addWidget(self.scan_key_btn)
        buttons_layout.addWidget(self.capture_btn)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.manage_students_btn)
        buttons_layout.addWidget(self.show_log_btn)
        buttons_layout.addWidget(self.analytics_btn)
        buttons_layout.addWidget(self.export_excel_btn)
        buttons_layout.addWidget(self.clear_results_btn)
        buttons_layout.addWidget(self.show_steps_btn)

        buttons_box.setLayout(buttons_layout)
        left_layout.addWidget(buttons_box)

        left_layout.addStretch()
        main_layout.addLayout(left_layout, 1)

        # -------- العمود الأيمن --------
        right_layout = QVBoxLayout()

        self.image_label = QLabel("Camera / Result Preview")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "border: 1px solid #888; background-color: #111; color: #ccc;"
        )
        self.image_label.setMinimumSize(700, 450)

        self.info_label = QLabel(
            "🎯 Start camera or load image, align the sheet, then scan key or grade."
        )
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 14px;")

        right_layout.addWidget(self.image_label)
        right_layout.addWidget(self.info_label)

        main_layout.addLayout(right_layout, 2)
        self.setCentralWidget(main_widget)

        # تحميل الطلاب في الـ ComboBox
        self.load_students_to_combo()

    # ---------- الطلاب في الـ ComboBox ----------
    def load_students_to_combo(self):
        rows = fetch_students()
        self.student_combo.clear()
        self.student_combo.addItem("— Select student —", None)
        for db_id, sid, sname, created_at in rows:
            label = f"{sid} - {sname}" if sid else sname
            self.student_combo.addItem(label, (sid, sname))

    def on_student_combo_changed(self, index: int):
        data = self.student_combo.itemData(index)
        if not data:
            return
        sid, sname = data
        self.student_id_edit.setText(str(sid or ""))
        self.student_name_edit.setText(str(sname or ""))

    # ---------- الكاميرا ----------
    def stop_camera(self):
        if self.cap is not None:
            self.timer.stop()
            self.cap.release()
            self.cap = None
        self.start_cam_btn.setText("🎥 Start Camera")

    def toggle_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = None
                QMessageBox.critical(self, "Error", "Could not open camera.")
                return
            self.timer.start(30)
            self.start_cam_btn.setText("⏹ Stop Camera")
            self.info_label.setText(
                "Move the sheet until it is aligned, then scan key or grade."
            )
        else:
            self.stop_camera()
            self.info_label.setText("Camera stopped.")

    def update_camera_frame(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        self.current_frame = frame.copy()
        self.show_cv_image(frame)

    # ---------- تحميل صورة من ملف ----------
    def load_image_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select OMR Sheet Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        if not file_path:
            return
        img = cv2.imread(file_path)
        if img is None:
            QMessageBox.warning(self, "Error", "Could not read image.")
            return
        self.stop_camera()
        self.current_frame = img
        self.show_cv_image(img)
        self.info_label.setText(f"Loaded image: {os.path.basename(file_path)}")

    # ---------- Scan Key ----------
    def scan_answer_key(self):
        if self.current_frame is None:
            QMessageBox.warning(
                self, "Warning",
                "No sheet image. Use camera or load an image first.",
            )
            return

        questions = self.questions_spin.value()
        choices = self.choices_spin.value()

        result_img, ans_list = detect_answer_key(self.current_frame, questions, choices)
        if not ans_list:
            QMessageBox.warning(
                self,
                "Warning",
                "Could not detect answer key. Check alignment and lighting.",
            )
            return

        self.correct_answers = ans_list
        self.ans_edit.setText(",".join(map(str, ans_list)))
        self.stop_camera()
        self.show_cv_image(result_img)
        self.info_label.setText(
            f"✅ Answer key scanned: {ans_list}"
        )

    # ---------- Capture & Grade ----------
    def capture_and_process(self):
        if self.current_frame is None:
            QMessageBox.warning(
                self,
                "Warning",
                "No sheet image. Start camera or load an image first.",
            )
            return

        questions = self.questions_spin.value()
        choices = self.choices_spin.value()
        ans_text = self.ans_edit.text().strip()

        try:
            ans_list = [int(x.strip()) for x in ans_text.split(",") if x.strip()]
        except ValueError:
            QMessageBox.warning(
                self, "Input error",
                "Correct answers format invalid. Use comma-separated numbers."
            )
            return

        if len(ans_list) != questions:
            QMessageBox.warning(
                self,
                "Input error",
                f"Number of answers ({len(ans_list)}) != questions ({questions}).",
            )
            return

        if any(a < 0 or a >= choices for a in ans_list):
            QMessageBox.warning(
                self,
                "Input error",
                "Each answer must be between 0 and choices-1.",
            )
            return

        result_img, score, marked, grading = process_omr(
            self.current_frame, questions, choices, ans_list
        )

        self.current_score = score
        self.current_answers = marked
        self.last_result_img = result_img  # نخزن الصورة مؤقتًا (لنحفظها عند حفظ النتيجة)
        self.stop_camera()

        self.show_cv_image(result_img)
        self.info_label.setText(f"✅ Graded – Score: {score:.2f} %")
        QMessageBox.information(self, "Score", f"Score: {score:.2f} %")

    def save_corrected_image(self, img_bgr, sid, exam):
        os.makedirs("Results", exist_ok=True)
        sid = sid or "unknown"
        exam = exam or "NOEXAM"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sid}_{exam}_{ts}.png"
        path = os.path.join("Results", filename)
        cv2.imwrite(path, img_bgr)
        print("Saved sheet image:", path)

    # ---------- عرض صورة ----------
    def show_cv_image(self, img_bgr):
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(
            pix.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    # ---------- حفظ النتيجة ----------
    def save_to_db(self):
        if self.current_score is None or self.current_answers is None:
            QMessageBox.warning(self, "Warning", "No graded result to save.")
            return

        sid = self.student_id_edit.text().strip()
        sname = self.student_name_edit.text().strip()
        exam = self.exam_code_edit.text().strip()

        if not exam:
            QMessageBox.warning(self, "Warning", "Please enter exam code.")
            return

        # حفظ في قاعدة البيانات
        save_result(sid, sname, exam, self.current_score, self.current_answers)

        # حفظ صورة الورقة فقط عند حفظ النتيجة
        if self.last_result_img is not None:
            self.save_corrected_image(self.last_result_img, sid, exam)

        QMessageBox.information(self, "Saved", "Result and sheet image saved.")

    # ---------- إدارة الطلاب ----------
    def open_students_dialog(self):
        dlg = StudentsDialog(self)
        dlg.exec()
        self.load_students_to_combo()

    # ---------- سجل النتائج ----------
    def show_results_log(self):
        exam = self.exam_code_edit.text().strip() or None
        rows = fetch_results(exam)

        dlg = QDialog(self)
        dlg.setWindowTitle("Results Log")
        dlg.resize(900, 500)
        layout = QVBoxLayout(dlg)

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["ID", "Student ID", "Student Name", "Exam Code",
             "Score", "Answers", "Created At"]
        )
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if c == 4:
                    item.setTextAlignment(Qt.AlignCenter)
                table.setItem(r, c, item)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.exec()

    # ---------- التحليل ----------
    def show_analytics(self):
        exam = self.exam_code_edit.text().strip() or None
        try:
            analytics.show_basic_stats(exam)
            analytics.show_score_histogram(exam)
        except Exception as e:
            QMessageBox.warning(
                self, "Analytics error",
                f"Could not show analytics:\n{e}"
            )

    # ---------- تصدير إلى Excel ----------
    def export_results_excel(self):
        exam = self.exam_code_edit.text().strip() or None
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", "results.xlsx", "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        try:
            analytics.export_results_to_excel(file_path, exam, only_basic=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{e}")
            return
        QMessageBox.information(self, "Exported", f"Exported to:\n{file_path}")

    # ---------- مسح كل النتائج ----------
    def clear_all_results_dialog(self):
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure you want to delete ALL results?\n(This will not delete students.)",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        clear_all_results()
        QMessageBox.information(self, "Done", "All results have been deleted.")

    # ---------- عرض خطوات OMR (Debug) ----------
    def show_omr_steps(self):
        if self.current_frame is None:
            QMessageBox.warning(
                self,
                "Warning",
                "No sheet image. Start camera or load an image first.",
            )
            return

        questions = self.questions_spin.value()
        choices = self.choices_spin.value()

        try:
            debug_img = get_debug_stack(self.current_frame, questions, choices)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Debug error",
                f"Could not generate debug image:\n{e}"
            )
            return

        self.stop_camera()
        self.show_cv_image(debug_img)
        self.info_label.setText("🔍 Showing OMR processing steps (debug image).")


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
