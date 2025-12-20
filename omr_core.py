# omr_core.py
import cv2
import numpy as np

# محاولة استيراد utilti.py الذي يحتوي على stackImages
try:
    import utilti
except ImportError:
    utilti = None

# حجم الورقة بعد التصحيح
WIDTH = 700
HEIGHT = 700


# ----------------- أدوات مساعدة للكونتور والـ Warp -----------------

def _rect_contours(contours):
    """اختيار الكونتورات التي تشبه المستطيل (4 نقاط) وترتيبها من الأكبر للأصغر."""
    rects = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < 2000:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            rects.append(approx)
    rects = sorted(rects, key=cv2.contourArea, reverse=True)
    return rects


def _reorder_points(pts):
    """إعادة ترتيب نقاط المستطيل: أعلى يسار، أعلى يمين، أسفل يسار، أسفل يمين."""
    pts = pts.reshape((4, 2))
    new_pts = np.zeros((4, 1, 2), dtype=np.int32)

    add = pts.sum(1)
    new_pts[0] = pts[np.argmin(add)]  # top-left
    new_pts[3] = pts[np.argmax(add)]  # bottom-right

    diff = np.diff(pts, axis=1)
    new_pts[1] = pts[np.argmin(diff)]  # top-right
    new_pts[2] = pts[np.argmax(diff)]  # bottom-left

    return new_pts


def _warp_perspective(img, pts):
    """تصحيح منظور ورقة واحدة (بناء على 4 نقاط)."""
    pts = _reorder_points(pts)
    src = np.float32(pts)
    dst = np.float32([[0, 0], [WIDTH, 0], [0, HEIGHT], [WIDTH, HEIGHT]])
    matrix = cv2.getPerspectiveTransform(src, dst)
    warp = cv2.warpPerspective(img, matrix, (WIDTH, HEIGHT))
    return warp, matrix


# ----------------- تقسيم الشبكة وحساب البكسلات -----------------

def _split_boxes(thresh_img, questions, choices):
    """
    تقسيم صورة الأسئلة (بعد الـ threshold) إلى مربعات صغيرة (سؤال × اختيار).
    يرجع قائمة طولها questions*choices.
    """
    rows = np.vsplit(thresh_img, questions)
    boxes = []
    for r in rows:
        cols = np.hsplit(r, choices)
        for box in cols:
            boxes.append(box)
    return boxes


def _extract_marked_indices(thresh_img, questions, choices):
    """
    يرجع مصفوفة قيم البكسلات + فهرس الخيار المختار لكل سؤال.
    """
    boxes = _split_boxes(thresh_img, questions, choices)
    pixel_vals = np.zeros((questions, choices), dtype=np.int32)

    r = c = 0
    for box in boxes:
        non_zero = cv2.countNonZero(box)
        pixel_vals[r, c] = non_zero
        c += 1
        if c == choices:
            c = 0
            r += 1

    # لكل سؤال نأخذ أعلى قيمة (أكثر فقاعة معبّأة)
    marked_indices = np.argmax(pixel_vals, axis=1).tolist()
    return pixel_vals, marked_indices


# ----------------- رسم الإجابات -----------------

def _draw_answers(img, marked_indices, correct_answers, questions, choices):
    """
    رسم دوائر على الورقة المصححة:
    - أخضر على الإجابات الصحيحة
    - أحمر على الإجابات الخاطئة
    - تظهير الإجابة الصحيحة إذا الطالب أخطأ
    """
    h, w = img.shape[:2]
    sec_w = int(w / choices)
    sec_h = int(h / questions)

    grading = []
    for q in range(questions):
        student_ans = marked_indices[q]
        correct_ans = correct_answers[q]

        # مركز فقاعة الطالب
        cx = int(student_ans * sec_w + sec_w / 2)
        cy = int(q * sec_h + sec_h / 2)

        if student_ans == correct_ans:
            grading.append(1)
            color = (0, 255, 0)  # أخضر
        else:
            grading.append(0)
            color = (0, 0, 255)  # أحمر

            # نعرض الإجابة الصحيحة بخط أخضر أصغر
            correct_cx = int(correct_ans * sec_w + sec_w / 2)
            correct_cy = int(q * sec_h + sec_h / 2)
            cv2.circle(img, (correct_cx, correct_cy), 25, (0, 255, 0), cv2.FILLED)

        cv2.circle(img, (cx, cy), 35, color, cv2.FILLED)

    return img, grading


# ----------------- واجهات رئيسية للـ GUI -----------------

def detect_answer_key(frame_bgr, questions, choices):
    """
    قراءة ورقة "إجابة نموذجية صحيحة" لاستخراج مفتاح الإجابات.
    ترجع:
      result_img (مع دوائر خضراء)
      ans_list   (قائمة الفهارس الصحيحة لكل سؤال: [0..choices-1])
    """
    img = cv2.resize(frame_bgr, (WIDTH, HEIGHT))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1)
    edges = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = _rect_contours(contours)
    if len(rects) == 0:
        return img, []

    # نأخذ أكبر مستطيل كأنه ورقة الأسئلة
    warp_color, _ = _warp_perspective(img, rects[0])
    warp_gray = cv2.cvtColor(warp_color, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(
        warp_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    _, marked_indices = _extract_marked_indices(thresh, questions, choices)

    # نعتبر هذه الإجابات كلها صحيحة (مفتاح)
    ans_list = marked_indices.copy()
    result_img, _ = _draw_answers(
        warp_color.copy(), marked_indices, ans_list, questions, choices
    )

    return result_img, ans_list


def process_omr(frame_bgr, questions, choices, correct_answers):
    """
    تصحيح ورقة طالب:
    ترجع:
      result_img (الورقة مع الدوائر + الدرجة مكتوبة)
      score      (من 0 إلى 100)
      marked     (إجابات الطالب كقائمة فهارس)
      grading    (0/1 لكل سؤال)
    """
    img = cv2.resize(frame_bgr, (WIDTH, HEIGHT))
    original = img.copy()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1)
    edges = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = _rect_contours(contours)
    if len(rects) == 0:
        # لم يتم العثور على ورقة واضحة
        return original, 0.0, [0] * questions, [0] * questions

    # الورقة الرئيسية (شبكة الأسئلة)
    warp_color, _ = _warp_perspective(img, rects[0])

    warp_gray = cv2.cvtColor(warp_color, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(
        warp_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    _, marked_indices = _extract_marked_indices(thresh, questions, choices)

    # رسم الإجابات
    result_warp, grading = _draw_answers(
        warp_color.copy(), marked_indices, correct_answers, questions, choices
    )

    score = (sum(grading) / float(questions)) * 100.0

    # كتابة الدرجة في أعلى الورقة
    text = f"{int(round(score))}%"
    cv2.putText(
        result_warp, text,
        (int(WIDTH * 0.05), int(HEIGHT * 0.1)),
        cv2.FONT_HERSHEY_SIMPLEX,
        2.0,
        (0, 255, 255),
        4,
        cv2.LINE_AA
    )

    # هنا نرجع الـ warp مباشرة (بحجم 700×700)
    result_img = result_warp

    return result_img, score, marked_indices, grading


def get_debug_stack(frame_bgr, questions, choices):
    """
    ترجع صورة واحدة فيها مراحل معالجة OMR مكدّسة:
    - الصورة الأصلية بعد الـ resize
    - صورة الرمادي + البلور
    - صورة الحواف (Canny)
    - الـ warp (إن وجد مستطيل)
    - صورة الـ threshold

    تعتمد على الدالة stackImages في utilti.py
    """
    if utilti is None:
        raise RuntimeError("utilti.py is not available or could not be imported.")

    img = cv2.resize(frame_bgr, (WIDTH, HEIGHT))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1)
    edges = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = _rect_contours(contours)

    warp_color = img.copy()
    thresh = gray.copy()

    if len(rects) > 0:
        warp_color, _ = _warp_perspective(img, rects[0])
        warp_gray = cv2.cvtColor(warp_color, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(
            warp_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

    # مصفوفة الصور لـ stackImages
    # (stackImages سيحوّل الصور الرمادية إلى BGR تلقائياً)
    imgArray = [
        [img, gray, blur],
        [edges, warp_color, thresh]
    ]

    debug_img = utilti.stackImages(0.4, imgArray)
    return debug_img
