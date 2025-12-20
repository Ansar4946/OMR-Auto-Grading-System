# 📄 OMR Auto Grading System
### GUI + Database + Analytics (Python)

An intelligent Optical Mark Recognition (OMR) system developed using **Python**,  
designed to automatically grade multiple-choice answer sheets using **Computer Vision**,  
a modern **Graphical User Interface (GUI)**, a **SQLite database**, and **data analytics**  
with Excel export support.

---

## 🚀 Project Overview (English)

This project aims to **automate the grading of paper-based multiple-choice exams**  
by scanning answer sheets using a camera or static image.

The system automatically:
- Detects the answer sheet  
- Extracts marked answers  
- Grades answers visually  
- Calculates the final score  
- Stores results in a database  
- Provides analytics and Excel export  

The system is suitable for:
- Schools  
- Universities  
- Training centers  
- Educational institutions  

---

## 🖥️ Graphical User Interface (GUI)

The system provides a modern and user-friendly GUI that allows the user to:

- Start and stop the camera  
- Load answer sheet images from disk  
- Select students from the database  
- Scan a correct answer sheet (Answer Key)  
- Grade student answer sheets visually  
- Save results and graded sheet images  
- Manage students (Add / Edit / Delete / Import)  
- View results log  
- Analyze scores statistically  
- Export results to Excel  

---

## ✨ System Features (English)

### 🧠 Intelligent Image Processing (OpenCV)
- Automatic detection of the answer sheet  
- Perspective correction (Warp transformation)  
- Sheet segmentation into a grid (Questions × Choices)  
- Accurate filled-bubble detection using pixel analysis  
- Visual grading feedback:
  - 🟢 Green for correct answers  
  - 🔴 Red for incorrect answers  

---

### 📝 Answer Key Support
- Scan a fully solved correct answer sheet  
- Automatically extract correct answers  
- Use the extracted key to grade student sheets  

---

### 👨‍🎓 Student Management
- Add, update, and delete students  
- Import students from an Excel file  
- Select students using a ComboBox  
- View the latest graded sheet image for each student  

---

### 🗂️ Database System (SQLite)
- Stores:
  - Student ID  
  - Student Name  
  - Exam Code  
  - Score  
  - Student Answers  
  - Date and time of grading  
- One-click clearing of all results  
- Local database (no server required)  

---

### 📊 Analytics & Statistics
- Calculate:
  - Average score  
  - Maximum score  
  - Minimum score  
  - Standard deviation  
- Display a histogram showing score distribution  

---

### 📥 Export Results to Excel
- Export final results to `.xlsx` format  
- Exported columns:
  - Student ID  
  - Student Name  
  - Exam Code  
  - Score  

---

### 🔍 Debug Mode (OMR Processing Steps)
- Visualize the image processing pipeline:
  - Original image  
  - Grayscale  
  - Blur  
  - Edge detection  
  - Perspective warp  
  - Threshold  
- Useful for educational purposes and debugging  

---

### 🖼️ Graded Sheet Image Storage
- Graded sheet images are saved **only when results are saved**  
- Image filename format:
- Stored images can be viewed later per student  

---

## 🛠️ Technologies Used

- Python 3  
- OpenCV  
- NumPy  
- PySide6  
- SQLite  
- Pandas  
- Matplotlib  

---

## 📂 Project Structure

```
OMR-Auto-Grading-System/
│
├── gui.py # GUI application
├── omr_core.py # OMR processing logic
├── utilti.py # Image processing visualization tools
├── db.py # Database management
├── analytics.py # Statistics & Excel export
├── Results/ # Saved graded sheet images
├── assets/ # README images
├── omr_results.db # SQLite database
└── README.md
```

---

## ▶️ How to Run

```bash
pip install opencv-python numpy pyside6 pandas matplotlib openpyxl
python gui.py
```
🎯 Conclusion (English)

Specialization:
Computer Science
Artificial Intelligence – Computer Vision – Educational Systems
---
## 📸 System Screenshots
![Analytics](https://raw.githubusercontent.com/alhattami0/OMR-Auto-Grading-System/main/assets/1.png)

---


📄 نظام التصحيح الآلي لورق الإجابات OMR
واجهة رسومية + قاعدة بيانات + تحليل (بايثون)

نظام ذكي لتصحيح أوراق الإجابة باستخدام لغة بايثون،
يعتمد على الرؤية الحاسوبية (OpenCV)، وواجهة رسومية حديثة باستخدام PySide6،
مع قاعدة بيانات SQLite وتحليل إحصائي وتصدير النتائج إلى Excel.

🚀 فكرة المشروع (عربي)

يهدف هذا المشروع إلى أتمتة عملية تصحيح الاختبارات الورقية
من نوع الاختيار من متعدد (Multiple Choice)،
عن طريق قراءة ورقة الإجابة باستخدام الكاميرا أو صورة ثابتة،
ثم استخراج الإجابات، تصحيحها تلقائيًا، حساب الدرجة،
وحفظ النتائج في قاعدة بيانات مع إمكانية تحليلها وتصديرها.

النظام مناسب لـ:

المدارس

الجامعات

المعاهد

المراكز التعليمية

🖥️ واجهة النظام (GUI)

يوفر النظام واجهة رسومية سهلة الاستخدام تتيح:

تشغيل وإيقاف الكاميرا

تحميل صورة ورقة الإجابة

اختيار الطالب من قاعدة البيانات

قراءة ورقة النموذج الصحيح

تصحيح ورقة الطالب وعرض النتيجة مباشرة

حفظ النتائج وصور الأوراق

إدارة بيانات الطلاب

عرض سجل النتائج

تحليل الدرجات إحصائيًا

تصدير النتائج إلى ملف Excel

✨ ميزات النظام (عربي)
🧠 المعالجة الذكية للصور

اكتشاف تلقائي لورقة الإجابة

تصحيح ميلان الورقة

تقسيم الورقة إلى شبكة (أسئلة × خيارات)

تحديد الخيار المظلل بدقة

تلوين الإجابات:

🟢 أخضر للإجابات الصحيحة

🔴 أحمر للإجابات الخاطئة

📝 دعم نموذج الإجابة

قراءة ورقة نموذجية محلولة بالكامل

استخراج الإجابات الصحيحة تلقائيًا

استخدام النموذج لتصحيح أوراق الطلاب

👨‍🎓 إدارة الطلاب

إضافة / تعديل / حذف الطلاب

استيراد الطلاب من ملف Excel

اختيار الطالب من قائمة منسدلة

عرض آخر صورة ورقة مصححة لكل طالب

🗂️ قاعدة البيانات

تخزين:

رقم الطالب

اسم الطالب

كود الاختبار

درجة الطالب

إجابات الطالب

تاريخ ووقت التصحيح

إمكانية مسح جميع النتائج بضغطة زر

قاعدة بيانات محلية بدون الحاجة إلى خادم

📊 التحليل الإحصائي

حساب متوسط الدرجات

أعلى وأقل درجة

الانحراف المعياري

عرض مخطط Histogram لتوزيع الدرجات

📥 تصدير النتائج إلى Excel

تصدير النتائج النهائية بصيغة .xlsx

الأعمدة:

رقم الطالب

اسم الطالب

كود الاختبار

الدرجة

🔍 وضع Debug

عرض مراحل معالجة الصورة:

الصورة الأصلية

التدرج الرمادي

التمويه

اكتشاف الحواف

تصحيح المنظور

العتبة الثنائية

🖼️ حفظ صور أوراق الإجابة

يتم حفظ صورة الورقة فقط عند حفظ النتيجة

تسمية الصورة بالشكل:

StudentID_ExamCode_Timestamp.png


إمكانية عرض الصورة لاحقًا لكل طالب

🎯 الخلاصة (عربي)

يوفر هذا النظام حلاً متكاملًا ودقيقًا لتصحيح الاختبارات الورقية
بسرعة عالية وتنظيم ممتاز للبيانات،
مما يجعله مناسبًا كمشروع جامعي، مشروع تخرج،
أو نظام تطبيقي للاستخدام في المؤسسات التعليمية.

👨‍💻 المطوّر

إياد الحطامي – Eyad Alhattami
GitHub: https://github.com/alhattami0

التخصص:
علوم حاسوب


⭐ Support the Project

If you like this project:

⭐ Star

🍴 Fork

📢 Share
