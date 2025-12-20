# analytics.py
from db import fetch_results


def _get_results_df(exam_code=None):
    """
    جلب النتائج وتحويلها إلى DataFrame باستخدام pandas.
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required for analytics. Install it with: pip install pandas") from e

    rows = fetch_results(exam_code)
    cols = [
        "id",
        "student_id",
        "student_name",
        "exam_code",
        "score",
        "answers",
        "created_at",
    ]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows, columns=cols)
    return df


def show_basic_stats(exam_code=None):
    """
    طباعة إحصائيات بسيطة عن الدرجات في الـ Terminal.
    """
    df = _get_results_df(exam_code)
    if df.empty:
        print("No results available for statistics.")
        return

    scores = df["score"]
    print("=== Basic Score Statistics ===")
    if exam_code:
        print(f"Exam code: {exam_code}")
    print(f"Count : {scores.count()}")
    print(f"Mean  : {scores.mean():.2f}")
    print(f"Min   : {scores.min():.2f}")
    print(f"Max   : {scores.max():.2f}")
    print(f"Std   : {scores.std():.2f}")
    print("==============================")


def show_score_histogram(exam_code=None):
    """
    رسم Histogram للدرجات باستخدام matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError("matplotlib is required for histogram. Install it with: pip install matplotlib") from e

    df = _get_results_df(exam_code)
    if df.empty:
        print("No results available for histogram.")
        return

    scores = df["score"]

    plt.figure()
    scores.plot(kind="hist", bins=10)
    plt.xlabel("Score")
    plt.ylabel("Number of Students")
    plt.title(f"Score Histogram ({exam_code or 'all exams'})")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()


def export_results_to_excel(path, exam_code=None, only_basic=True):
    """
    تصدير النتائج إلى ملف Excel.
    إذا only_basic=True سيتم تصدير الأعمدة:
      student_id, student_name, exam_code, score
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas/openpyxl are required. Install them with: pip install pandas openpyxl") from e

    df = _get_results_df(exam_code)
    if df.empty:
        raise ValueError("No results to export.")

    if only_basic:
        df = df[["student_id", "student_name", "exam_code", "score"]]

    df.to_excel(path, index=False)
