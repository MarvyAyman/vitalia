from django.db import models
from django.contrib.auth.models import User

# ==============================================================
# 1. CATEGORY & SUBSCRIPTION ENTITIES
# ==============================================================

class University(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="University Name",
        help_text="Full official name of the university or training hospital."
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "1. Universities"
        ordering = ["name"]


class AcademicYear(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Academic Year Name",
        help_text="e.g., 'Year 1', 'Year 2', 'Year 3 Prep'."
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Academic Year"
        verbose_name_plural = "2. Academic Years"
        ordering = ["name"]


class StudentProfile(models.Model):
    """
    Extends the standard Django User table to manage explicit permission limits.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    university = models.ForeignKey(University, on_delete=models.PROTECT, verbose_name="Enrolled University")
    allowed_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, verbose_name="Permitted Curriculum Year")

    def __str__(self):
        return f"{self.user.username} - {self.university.name} ({self.allowed_year.name})"


class Course(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="courses")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="courses", null=True, blank=True)
    name = models.CharField(max_length=150, verbose_name="Course Name")

    def __str__(self):
        return f"{self.name} ({self.university.name} - {self.academic_year.name if self.academic_year else 'N/A'})"

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "3. Courses"


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    name = models.CharField(max_length=150, verbose_name="Module Name")

    def __str__(self):
        return f"{self.name} — {self.course.name}"

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "4. Modules"


# ==============================================================
# 2. MCQ QUESTION MANAGEMENT WITH MULTILINGUAL METADATA
# ==============================================================

class Question(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="questions")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="questions", null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="questions")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="questions")
    lecture = models.CharField(max_length=200, verbose_name="Lecture Reference Title", db_index=True)

    # Bilingual content — English primary, French secondary
    question_text = models.TextField(verbose_name="Question (English)")
    question_text_fr = models.TextField(blank=True, null=True, verbose_name="Question (French)")

    correct_option = models.CharField(
        max_length=20,
        verbose_name="Correct Option(s)",
        help_text=(
            "Use letters or numbers, separated by commas — case-insensitive. "
            "Examples: 'A', 'a', 'A,C', 'a,c', '1', '1,3'. "
            "A/1 = first option, B/2 = second, C/3 = third, and so on."
        )
    )

    explanation = models.TextField(blank=True, null=True, verbose_name="Explanation (English)")
    explanation_fr = models.TextField(blank=True, null=True, verbose_name="Explanation (French)")

    def __str__(self):
        return self.question_text[:60] + "..."

    class Meta:
        verbose_name = "MCQ Question"
        verbose_name_plural = "5. MCQ Questions"


class QuestionOption(models.Model):
    """
    A single answer choice belonging to a Question.
    Options are ordered by insertion (pk). The correct_option field on Question
    uses letters (A, B, C…) or numbers (1, 2, 3…) — both accepted, case-insensitive.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=512, verbose_name="Option Text (English)")
    text_fr = models.CharField(max_length=512, blank=True, null=True, verbose_name="Option Text (French)")

    class Meta:
        verbose_name = "Question Option"
        verbose_name_plural = "Question Options"
        ordering = ["pk"]

    def __str__(self):
        return f"Option for QID-{self.question.id}: {self.text[:60]}"


class SavedNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_notes")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    student_note = models.TextField(blank=True, null=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Saved Bookmark"
        verbose_name_plural = "6. Saved Bookmarks"


# ==============================================================
# 3. CLINICAL DIAGNOSIS SIMULATOR
# ==============================================================

class DiagnosisCase(models.Model):
    """
    Represents a clinical case vignette used in the progressive diagnosis simulator.
    Hints are stored in the related DiagnosisHint model and unlock step-by-step
    as wrong answers are logged.
    """
    case_title = models.CharField(
        max_length=200,
        verbose_name="Case Vignette Title",
        help_text="A short title (e.g., 'A 54-year-old presenting with sharp substernal distress')."
    )

    # Broad category filter (e.g., Cardiologie, Neurologie, Pneumologie)
    specialty_category = models.CharField(
        max_length=100,
        default="General Medicine",
        verbose_name="Medical Specialty",
        help_text="Broad filter parameter. Examples: 'Cardiologie', 'Neurologie', 'Gastro-entérologie'."
    )

    case_description = models.TextField(
        verbose_name="Initial Case Presentation (English)",
        help_text="Baseline status shown to the doctor immediately on game launch (Vitals, primary complaint)."
    )
    case_description_fr = models.TextField(
        blank=True, null=True,
        verbose_name="Initial Case Presentation (French)",
    )

    correct_diagnosis = models.CharField(
        max_length=150,
        verbose_name="Correct Diagnosis",
        help_text="The exact term. Example: 'Acute Myocardial Infarction'."
    )
    correct_diagnosis_fr = models.CharField(
        max_length=150,
        blank=True, null=True,
        verbose_name="Correct Diagnosis (French)",
        help_text="French equivalent. Example: 'Infarctus du myocarde'."
    )

    prise_on_charge = models.TextField(
        default="",
        blank=True,
        verbose_name="Management (English)",
    )
    prise_on_charge_fr = models.TextField(
        default="",
        blank=True,
        verbose_name="Management (French)",
    )

    is_active = models.BooleanField(default=True, verbose_name="Active Status Track")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def hint_count(self):
        """Calculates dynamic hint counts for Django list_display metrics without hardcoded fields."""
        return self.hints.count()

    def __str__(self):
        return f"[{self.specialty_category}] {self.case_title}"

    class Meta:
        verbose_name = "Diagnosis Game Case"
        verbose_name_plural = "7. Diagnosis Game Cases"


class DiagnosisHint(models.Model):
    """
    A single progressive hint belonging to a DiagnosisCase.
    Hints unlock one-by-one as the student submits wrong diagnoses,
    revealed in insertion order (pk).
    """
    case = models.ForeignKey(DiagnosisCase, on_delete=models.CASCADE, related_name="hints")
    text = models.CharField(max_length=512, verbose_name="Hint Text (English)")
    text_fr = models.CharField(max_length=512, blank=True, null=True, verbose_name="Hint Text (French)")

    class Meta:
        verbose_name = "Diagnosis Hint"
        verbose_name_plural = "Diagnosis Hints"
        ordering = ["pk"]

    def __str__(self):
        return f"Hint for Case #{self.case.id}: {self.text[:60]}"


# ==============================================================
# 4. STUDENT PROGRESS TRACKING (MCQ + DIAGNOSIS)
# ==============================================================

class UserAnswer(models.Model):
    """
    Logs every MCQ question the student has answered during an exam session.
    One row per (user, question) — updated in-place on re-attempt.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="answers", db_index=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="user_answers")

    # The zero-based index/indices the student last chose, stored as JSON string e.g. "[0]" or "[0,2]"
    chosen_indices = models.CharField(max_length=64, default="[]")
    is_correct = models.BooleanField(default=False)

    # --- Spaced-repetition readiness flags ---
    needs_review = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Needs Spaced-Repetition Review",
        help_text="Auto-set to True when the student answers incorrectly. Reset to False once they answer correctly."
    )
    flagged = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Manually Flagged by Student",
        help_text="Student-controlled bookmark — marks a question for intentional later review."
    )

    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Answer"
        verbose_name_plural = "8. User Answers (MCQ Progress)"
        unique_together = [("user", "question")]
        indexes = [
            models.Index(fields=["user", "question"], name="idx_useranswer_user_question"),
            models.Index(fields=["user", "needs_review"], name="idx_useranswer_needs_review"),
        ]

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{self.user.username} [{status}] Q{self.question_id}"


class DiagnosisCaseProgress(models.Model):
    """
    Saves the student's state for each clinical diagnosis case they have interacted with.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="diagnosis_progress", db_index=True)
    case = models.ForeignKey(DiagnosisCase, on_delete=models.CASCADE, related_name="progress_records")

    hints_unlocked_count = models.PositiveSmallIntegerField(default=0)
    is_solved = models.BooleanField(default=False)
    attempts_count = models.PositiveSmallIntegerField(default=0)

    # --- Spaced-repetition readiness flags ---
    needs_review = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Needs Spaced-Repetition Review",
        help_text="Auto-set to True when the student exhausts all 6 attempts without solving."
    )
    flagged = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Manually Flagged by Student",
    )

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Diagnosis Case Progress"
        verbose_name_plural = "9. Diagnosis Case Progress"
        unique_together = [("user", "case")]
        indexes = [
            models.Index(fields=["user", "case"], name="idx_diagprogress_user_case"),
            models.Index(fields=["user", "needs_review"], name="idx_diagprogress_needs_review"),
        ]

    def __str__(self):
        status = "solved" if self.is_solved else f"{self.attempts_count} attempts"
        return f"{self.user.username} — Case {self.case_id} ({status})"