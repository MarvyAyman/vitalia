from django.contrib import admin
from .models import (
    University, AcademicYear, StudentProfile,
    Course, Module, Question, QuestionOption,
    SavedNote, DiagnosisCase, DiagnosisHint,
)


# ==============================================================
# INLINES
# ==============================================================

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 5
    min_num = 2
    max_num = 10
    fields = ("text", "text_fr")
    ordering = ("pk",)


class DiagnosisHintInline(admin.TabularInline):
    model = DiagnosisHint
    extra = 6
    min_num = 0
    max_num = 12
    fields = ("text", "text_fr")
    ordering = ("pk",)


# ==============================================================
# MODEL ADMINS
# ==============================================================

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "university", "allowed_year")
    list_filter = ("university", "allowed_year")
    search_fields = ("user__username", "user__email")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "university", "academic_year")
    list_filter = ("university", "academic_year")
    search_fields = ("name",)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("name", "course")
    list_filter = ("course__university", "course")
    search_fields = ("name",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question_excerpt", "university", "academic_year", "module", "lecture", "option_count")
    list_filter = ("university", "academic_year", "module")
    search_fields = ("question_text", "lecture")
    inlines = [QuestionOptionInline]

    readonly_fields = ()
    fieldsets = (
        ("Question Info", {
            "fields": ("university", "academic_year", "course", "module", "lecture")
        }),
        ("Content — English (Primary)", {
            "fields": ("question_text", "correct_option", "explanation"),
            "description": (
                "Set <strong>Correct Option(s)</strong> using letters or numbers, comma-separated. "
                "Examples: <code>A</code>, <code>a,c</code>, <code>A,C</code>, <code>1,3</code>. "
                "A/1 = first option in the list below, B/2 = second, and so on."
            ),
        }),
        ("Content — French (Secondary)", {
            "fields": ("question_text_fr", "explanation_fr"),
            "classes": ("collapse",),
            "description": "Optional French translation shown below the English in the quiz UI.",
        }),
    )

    def question_excerpt(self, obj):
        return obj.question_text[:60] + "..." if len(obj.question_text) > 60 else obj.question_text
    question_excerpt.short_description = "Question Text Preview"

    def option_count(self, obj):
        count = obj.options.count()
        return f"{count} option{'s' if count != 1 else ''}"
    option_count.short_description = "Options"


@admin.register(SavedNote)
class SavedNoteAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "saved_at")
    list_filter = ("user", "saved_at")
    readonly_fields = ("saved_at",)


@admin.register(DiagnosisCase)
class DiagnosisCaseAdmin(admin.ModelAdmin):
    list_display = ("case_title", "specialty_category", "correct_diagnosis", "hint_count", "is_active", "created_at")
    list_filter = ("is_active", "specialty_category")
    search_fields = ("case_title", "correct_diagnosis")
    readonly_fields = ("created_at",)
    inlines = [DiagnosisHintInline]

    fieldsets = (
        ("Case Identity", {
            "fields": ("case_title", "specialty_category", "is_active")
        }),
        ("Clinical Scenario — English (Primary)", {
            "fields": ("case_description",),
            "description": "Baseline presentation shown immediately when the case loads."
        }),
        ("Clinical Scenario — French (Secondary)", {
            "fields": ("case_description_fr",),
            "classes": ("collapse",),
        }),
        ("Answer & Management — English", {
            "fields": ("correct_diagnosis", "prise_on_charge"),
        }),
        ("Answer & Management — French", {
            "fields": ("correct_diagnosis_fr", "prise_on_charge_fr"),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    def hint_count(self, obj):
        count = obj.hints.count()
        return f"{count} hint{'s' if count != 1 else ''}"
    hint_count.short_description = "Hints"