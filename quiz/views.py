from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
import json
import random
from .models import (
    University, AcademicYear, Course, Module, Question, SavedNote,
    DiagnosisCase, UserAnswer, DiagnosisCaseProgress,
)


@login_required
def dashboard_view(request):
    try:
        profile = request.user.profile
        user_university = profile.university
        user_year = profile.allowed_year
    except AttributeError:
        return render(request, "quiz/error.html", {"message": "No student profile configuration linked to your profile."})

    # Pull the 5 most recent bookmarks and select the related question records safely
    saved_bookmarks = (
        SavedNote.objects
        .filter(user=request.user)
        .select_related('question', 'question__course', 'question__module')
        .order_by('-saved_at')[:5]
    )

    context = {
        "profile": profile,
        "user_university": user_university,
        "user_year": user_year,
        "saved_bookmarks": saved_bookmarks,
    }
    return render(request, "quiz/dashboard.html", context)


@login_required
def mcq_quiz_config_view(request):
    """
    Renders the configuration page shell with pre-filtered courses
    based on the logged-in student's university track.
    """
    user_profile = request.user.profile
    user_univ = user_profile.university
    user_year = user_profile.allowed_year

    allowed_courses = Course.objects.filter(university=user_univ, academic_year=user_year)

    context = {
        "university": user_univ,
        "academic_year": user_year,
        "courses": allowed_courses,
    }
    return render(request, "quiz/quiz_config.html", context)


@login_required
def api_filter_options(request):
    """
    Internal API endpoint providing cascading filters directly from the database
    without causing full page reloads.
    """
    user_profile = request.user.profile
    course_id = request.GET.get("course")
    module_id = request.GET.get("module")
    lang = request.GET.get("lang", "EN")

    data = {"modules": [], "lectures": []}

    if course_id and not module_id:
        modules = Module.objects.filter(course_id=course_id)
        data["modules"] = [{"id": m.id, "name": m.name} for m in modules]

    elif module_id:
        lectures = Question.objects.filter(
            university=user_profile.university,
            academic_year=user_profile.allowed_year,
            module_id=module_id,
            language=lang
        ).values_list('lecture', flat=True).distinct()

        data["lectures"] = list(lectures)

    return JsonResponse(data)


@login_required
def start_exam_engine_api(request):
    """
    Provides randomly shuffled matching questions for chosen criteria, limited
    strictly by the slider volume configuration parameter.

    Options are fetched from the related QuestionOption model (One-to-Many),
    ordered by the `order` field so display sequence is deterministic.
    correct_option stores 1-based order numbers (e.g. "1,3") which are converted
    to zero-based indices so the existing frontend JS contract is preserved.
    """
    user_profile = request.user.profile

    course_id = request.GET.get("course")
    module_id = request.GET.get("module")
    lecture_title = request.GET.get("lecture")
    lang = request.GET.get("lang", "EN")

    try:
        requested_limit = int(request.GET.get("limit", 20))
    except ValueError:
        requested_limit = 20

    questions_pool = Question.objects.filter(
        university=user_profile.university,
        academic_year=user_profile.allowed_year,
        language=lang
    ).prefetch_related("options")   # Prefetch options to avoid N+1 queries

    if course_id:
        questions_pool = questions_pool.filter(course_id=course_id)
    if module_id:
        questions_pool = questions_pool.filter(module_id=module_id)
    if lecture_title:
        questions_pool = questions_pool.filter(lecture=lecture_title)

    # ── Resume logic: exclude questions the student has already answered ──
    answered_ids = UserAnswer.objects.filter(
        user=request.user,
        question__in=questions_pool
    ).values_list("question_id", flat=True)

    questions_pool = questions_pool.exclude(id__in=answered_ids)

    questions_data = list(questions_pool.order_by('?'))
    selected_questions = questions_data[:requested_limit]

    payload = []
    for q in selected_questions:
        # Options ordered by pk (insertion order = the order admin added them)
        ordered_options = list(q.options.order_by("pk"))
        option_texts = [opt.text for opt in ordered_options]

        # Parse correct_option — accepts letters (A/a/B/b…) or numbers (1/2/3…),
        # any case, comma-separated. Both map to zero-based indices.
        # Examples: "A" → [0], "a,C" → [0,2], "1,3" → [0,2]
        correct_indices = []
        for raw in q.correct_option.split(","):
            token = raw.strip().upper()
            if not token:
                continue
            if token.isalpha() and len(token) == 1:
                # Letter: A→0, B→1, C→2 …
                idx = ord(token) - ord('A')
            elif token.isdigit():
                # Number: 1→0, 2→1, 3→2 …
                idx = int(token) - 1
            else:
                continue
            if 0 <= idx < len(option_texts):
                correct_indices.append(idx)

        payload.append({
            "id": q.id,
            "text": q.question_text,
            "options": option_texts,           # Dynamic list — length matches however many options exist
            "correct_list": correct_indices,   # Zero-based indices
            "explanation": q.explanation or ""
        })

    return JsonResponse({"status": "success", "questions": payload})


@login_required
@require_POST
def save_question_note_api(request):
    try:
        data = json.loads(request.body)
        question_id = data.get("question_id")
        note_text = data.get("note", "").strip()

        question_item = get_object_or_404(Question, id=question_id)

        saved_note, created = SavedNote.objects.update_or_create(
            user=request.user,
            question=question_item,
            defaults={"student_note": note_text}
        )
        return JsonResponse({"status": "success", "message": "Note successfully saved!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
@require_POST
def save_user_answer_api(request):
    """
    Records (or updates) the student's answer for a single MCQ question.

    Payload (JSON):
        question_id     : int   — PK of the Question
        chosen_indices  : list  — zero-based index/indices selected, e.g. [0] or [0, 2]
        is_correct      : bool  — evaluated on the frontend, mirrored here for efficiency

    Behaviour:
        • Uses update_or_create so re-attempting a question simply overwrites the record.
        • needs_review is set to True when the answer is wrong, and cleared when correct.
    """
    try:
        data = json.loads(request.body)
        question_id = data.get("question_id")
        chosen_indices = data.get("chosen_indices", [])
        is_correct = bool(data.get("is_correct", False))

        question_item = get_object_or_404(Question, id=question_id)

        UserAnswer.objects.update_or_create(
            user=request.user,
            question=question_item,
            defaults={
                "chosen_indices": json.dumps(chosen_indices),
                "is_correct": is_correct,
                "needs_review": not is_correct,
            }
        )
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
def diagnosis_simulator_view(request):
    """Renders standalone clinical diagnosis simulator dashboard page."""
    return render(request, "quiz/diagnosis_simulator.html")


@login_required
def get_random_diagnosis_case_api(request):
    """
    Fetches a diagnostic case vignette filtered by specialty.

    Supports sequential navigation via current_id + direction params:
      - direction=next  → loads the next case by PK after current_id
      - direction=prev  → loads the previous case by PK before current_id
      - no direction    → loads the first active case (ordered by PK)

    Returns status=empty when no further cases exist in the requested direction,
    signalling the frontend to trigger the completion screen.

    Hints are returned as an ordered list of objects: [{order, text}, …].
    The frontend reveals hint[n] after the (n+1)-th wrong submission.
    """
    category = request.GET.get("category", "ALL").strip()
    current_id = request.GET.get("current_id", "")
    direction = request.GET.get("direction", "")

    cases = DiagnosisCase.objects.filter(is_active=True).prefetch_related("hints")
    if category and category.upper() != "ALL":
        cases = cases.filter(specialty_category__iexact=category)

    # Sequential navigation
    if current_id and direction:
        try:
            current_id_int = int(current_id)
        except ValueError:
            current_id_int = 0

        if direction == "next":
            case_item = cases.filter(pk__gt=current_id_int).order_by("pk").first()
        elif direction == "prev":
            case_item = cases.filter(pk__lt=current_id_int).order_by("-pk").first()
        else:
            case_item = cases.order_by("pk").first()
    else:
        # Initial load — jump to the first unsolved case for this student.
        # A case is "solved" when DiagnosisCaseProgress.is_solved=True OR
        # attempts_count >= 6 (exhausted). Skip both so the student resumes
        # where they left off rather than always restarting from case 1.
        finished_case_ids = DiagnosisCaseProgress.objects.filter(
            user=request.user,
        ).filter(
            models.Q(is_solved=True) | models.Q(attempts_count__gte=6)
        ).values_list("case_id", flat=True)

        first_unsolved = cases.exclude(pk__in=finished_case_ids).order_by("pk").first()
        # If every case is finished, fall back to the first case so the student
        # can still navigate and review — the completion screen handles the UX.
        case_item = first_unsolved if first_unsolved else cases.order_by("pk").first()

    if not case_item:
        return JsonResponse({
            "status": "empty",
            "message": "No active clinical scenarios found for this specialty filter selection."
        })

    # Build ordered hint list sorted by the `order` field
    hints = [
        {
            "order": i + 1,
            "text": hint.text,
        }
        for i, hint in enumerate(case_item.hints.order_by("pk"))
    ]

    # Check if there is a next/prev case so frontend can grey out nav arrows accordingly
    has_next = cases.filter(pk__gt=case_item.pk).exists()
    has_prev = cases.filter(pk__lt=case_item.pk).exists()

    # ── Fetch this student's saved progress for the case ──
    progress = DiagnosisCaseProgress.objects.filter(
        user=request.user, case=case_item
    ).first()

    return JsonResponse({
        "status": "success",
        "id": case_item.id,
        "title": case_item.case_title,
        "category": case_item.specialty_category,
        "description": case_item.case_description,
        "hints": hints,          # [{order, text}, …] — variable length
        "answer": case_item.correct_diagnosis,
        "management": case_item.prise_on_charge,
        "has_next": has_next,
        "has_prev": has_prev,
        # ── Saved progress state for this student ──
        "progress": {
            "hints_unlocked_count": progress.hints_unlocked_count if progress else 0,
            "is_solved": progress.is_solved if progress else False,
            "attempts_count": progress.attempts_count if progress else 0,
        },
    })


@login_required
def get_medical_terms_autocomplete_api(request):
    """Retrieves standard database targets to complement remote CDN lookup engines."""
    db_diagnoses = list(
        DiagnosisCase.objects.filter(is_active=True)
        .values_list('correct_diagnosis', flat=True)
        .distinct()
    )
    return JsonResponse({"status": "success", "terms": db_diagnoses})


@login_required
@require_POST
def save_diagnosis_progress_api(request):
    """
    Saves (or updates) the student's in-progress state for a single diagnosis case.
    Called by the frontend after every guess attempt and after a correct solve.

    Payload (JSON):
        case_id              : int   — PK of the DiagnosisCase
        hints_unlocked_count : int   — how many hint strips are currently revealed (0-6)
        is_solved            : bool  — True if the student guessed correctly
        attempts_count       : int   — total wrong attempts so far

    Behaviour:
        • All cases remain accessible via Prev/Next — this only saves state, never hides cases.
        • needs_review is set to True when the student exhausts 6 attempts without solving.
    """
    try:
        data = json.loads(request.body)
        case_id = data.get("case_id")
        hints_unlocked_count = int(data.get("hints_unlocked_count", 0))
        is_solved = bool(data.get("is_solved", False))
        attempts_count = int(data.get("attempts_count", 0))

        case_item = get_object_or_404(DiagnosisCase, id=case_id)

        # needs_review: exhausted all attempts without solving
        needs_review = (attempts_count >= 6 and not is_solved)

        DiagnosisCaseProgress.objects.update_or_create(
            user=request.user,
            case=case_item,
            defaults={
                "hints_unlocked_count": hints_unlocked_count,
                "is_solved": is_solved,
                "attempts_count": attempts_count,
                "needs_review": needs_review,
            }
        )
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)