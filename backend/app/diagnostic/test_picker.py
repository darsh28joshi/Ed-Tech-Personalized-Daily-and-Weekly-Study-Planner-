"""
TestPicker — Pure Logic (no DB/network calls)

Handles picking the 60 questions for the diagnostic test:
- 15 Aptitude questions (compulsory, slab 5-7, across categories)
- 45 Academic questions partitioned by standard based on entry point:
  - START_OF_YEAR: 18 Std 5, 27 Std 6, 0 Std 7
  - MID_SEMESTER: 10 Std 5, 15 Std 6, 20 Std 7
  - END_OF_TERM: 0 questions (direct transition to planner)
"""

import logging
import random
from typing import List, Dict, Tuple
from app.onboarding.entry_point_resolver import EntryPoint

logger = logging.getLogger(__name__)


class TestPicker:
    TOTAL_APTITUDE = 15
    TOTAL_ACADEMIC = 45

    @classmethod
    def get_standard_allocation(cls, entry_point: EntryPoint) -> Dict[int, int]:
        """
        Returns {standard_number: count} for academic questions.
        - START_OF_YEAR: 18 questions from Std 5, 27 questions from Std 6
        - MID_SEMESTER: 10 questions from Std 5, 15 questions from Std 6, 20 questions from Std 7
        - END_OF_TERM: 0 questions
        """
        if entry_point == EntryPoint.START_OF_YEAR:
            return {5: 18, 6: 27, 7: 0}
        elif entry_point == EntryPoint.MID_SEMESTER:
            return {5: 10, 6: 15, 7: 20}
        else:
            return {5: 0, 6: 0, 7: 0}

    @classmethod
    def get_subject_allocation(cls, total_questions: int, subjects: List[dict]) -> Dict[int, int]:
        """
        Distributes total_questions across subjects as evenly as possible.
        Uses round-robin remainder distribution sorted by subject_id.
        """
        if not subjects or total_questions <= 0:
            return {}

        n_subjects = len(subjects)
        base = total_questions // n_subjects
        remainder = total_questions % n_subjects

        # Sort by subject_id to be deterministic
        sorted_subjects = sorted(subjects, key=lambda s: s['subject_id'])
        allocation = {}
        for i, s in enumerate(sorted_subjects):
            extra = 1 if i < remainder else 0
            allocation[s['subject_id']] = base + extra

        return allocation

    @classmethod
    def sample_difficulty(cls, pool: List[dict], count: int) -> Tuple[List[dict], int]:
        """
        Samples count questions from pool aiming for 30% Easy, 45% Average, 25% Difficult.
        Returns (selected_questions, shortfall).
        
        If shortfall occurs (pool doesn't have enough questions of requested difficulty),
        it relaxes difficulty bounds to pull from other difficulties.
        """
        if count <= 0:
            return [], 0

        if len(pool) <= count:
            # Take all questions in pool
            return list(pool), count - len(pool)

        easy = [q for q in pool if (q['difficulty'].lower() if q.get('difficulty') else 'average') == 'easy']
        average = [q for q in pool if (q['difficulty'].lower() if q.get('difficulty') else 'average') == 'average']
        difficult = [q for q in pool if (q['difficulty'].lower() if q.get('difficulty') else 'average') == 'difficult']

        target_easy = round(count * 0.30)
        target_diff = round(count * 0.25)
        target_avg = count - target_easy - target_diff

        selected = []
        
        # Helper to sample from subpool
        def draw(subpool, target_count):
            if target_count <= 0:
                return 0
            take = min(len(subpool), target_count)
            chosen = random.sample(subpool, take)
            selected.extend(chosen)
            for item in chosen:
                subpool.remove(item)
            return target_count - take

        rem_easy = draw(easy, target_easy)
        rem_avg = draw(average, target_avg)
        rem_diff = draw(difficult, target_diff)

        # Fallback 1: Relax difficulty bounds within the same subject pool
        shortfall = rem_easy + rem_avg + rem_diff
        if shortfall > 0:
            remaining_pool = easy + average + difficult
            draw(remaining_pool, shortfall)

        actual_shortfall = count - len(selected)
        return selected, actual_shortfall

    @classmethod
    def pick_questions(
        cls,
        entry_point: EntryPoint,
        academic_pool: List[dict],  # Questions with standard_number, subject_id, subject_name, chapter_number, difficulty
        aptitude_pool: List[dict],  # Questions with category, difficulty
        syllabus_progress: Dict[int, int],  # Maps subject_id -> last_taught_chapter_number for Std 7
        subjects_by_std: Dict[int, List[dict]],  # Maps standard_number -> list of subjects
    ) -> List[dict]:
        """
        Selects and orders 49 diagnostic questions (7 sections x 7 questions each) based on entry point.
        """
        if entry_point == EntryPoint.END_OF_TERM:
            return []

        # 1. Select Aptitude questions: exactly 7 questions
        aptitude_selected = []
        if aptitude_pool:
            drawn, sf = cls.sample_difficulty(aptitude_pool, 7)
            for q in drawn:
                aptitude_selected.append({
                    "question_id": q['question_id'],
                    "source": "APTITUDE",
                    "section": "Aptitude section",
                    "difficulty": q['difficulty']
                })

        # Academic sections mapping
        ACADEMIC_SECTIONS = [
            "Mathematics",
            "Science",
            "History and Civics",
            "Geography",
            "Hindi",
            "Marathi"
        ]

        def get_subject_section(subj_name: str) -> str:
            name_lower = subj_name.lower()
            if "math" in name_lower:
                return "Mathematics"
            elif "science" in name_lower or "environmental studies part 1" in name_lower:
                return "Science"
            elif "history" in name_lower or "civics" in name_lower or "environmental studies part 2" in name_lower:
                return "History and Civics"
            elif "geography" in name_lower:
                return "Geography"
            elif "hindi" in name_lower:
                return "Hindi"
            elif "marathi" in name_lower:
                return "Marathi"
            return "Other"

        academic_selected = []

        for section in ACADEMIC_SECTIONS:
            section_pool = [q for q in academic_pool if get_subject_section(q['subject_name']) == section]
            
            # Determine standard allocation
            if entry_point == EntryPoint.START_OF_YEAR:
                stds_to_draw = [5, 6]
                std_targets = {5: 3, 6: 4}
            elif entry_point == EntryPoint.MID_SEMESTER:
                stds_to_draw = [5, 6, 7]
                std_targets = {5: 2, 6: 2, 7: 3}
            else:
                stds_to_draw = []
                std_targets = {}

            section_selected = []
            shortfall = 0

            for std_num in stds_to_draw:
                target = std_targets.get(std_num, 0) + shortfall
                shortfall = 0

                std_pool = [q for q in section_pool if q['standard_number'] == std_num]

                if std_num == 7:
                    # Apply pacing filter
                    std_pool_filtered = []
                    for q in std_pool:
                        last_taught = syllabus_progress.get(q['subject_id'], 0)
                        if q['chapter_number'] <= last_taught:
                            std_pool_filtered.append(q)
                    std_pool = std_pool_filtered

                drawn, sf = cls.sample_difficulty(std_pool, target)
                section_selected.extend(drawn)
                shortfall = sf

            # Fallback cascade: Borrow from remaining section questions if target standard pools were short
            if shortfall > 0:
                remaining_pool = [q for q in section_pool if q not in section_selected]
                remaining_pool_filtered = []
                for q in remaining_pool:
                    if q['standard_number'] == 7:
                        last_taught = syllabus_progress.get(q['subject_id'], 0)
                        if q['chapter_number'] <= last_taught:
                            remaining_pool_filtered.append(q)
                    else:
                        remaining_pool_filtered.append(q)

                borrowed, sf = cls.sample_difficulty(remaining_pool_filtered, shortfall)
                section_selected.extend(borrowed)
                shortfall = sf

            if shortfall > 0:
                logger.error(f"Shortfall of {shortfall} questions for section {section} could not be resolved!")

            # Record chosen questions tagged with their custom section name
            for q in section_selected:
                academic_selected.append({
                    "question_id": q['question_id'],
                    "source": "ACADEMIC",
                    "section": section,
                    "difficulty": q['difficulty']
                })

        # Format and order questions grouped by section, and difficulty ordered within section
        final_questions = []
        order = 1

        # 1. Aptitude section block
        for q in aptitude_selected:
            final_questions.append({
                "source": "APTITUDE",
                "section": "APTITUDE",
                "question_id": q['question_id'],
                "order": order
            })
            order += 1

        # 2. Academic section blocks
        for section in ACADEMIC_SECTIONS:
            sec_qs = [q for q in academic_selected if q['section'] == section]
            
            def get_diff(item):
                d = item.get('difficulty')
                return d.lower() if d else 'average'
            
            easy_qs = [q for q in sec_qs if get_diff(q) == 'easy']
            avg_qs = [q for q in sec_qs if get_diff(q) == 'average']
            diff_qs = [q for q in sec_qs if get_diff(q) == 'difficult']

            random.shuffle(easy_qs)
            random.shuffle(avg_qs)
            random.shuffle(diff_qs)

            ordered = easy_qs + avg_qs + diff_qs
            for q in ordered:
                final_questions.append({
                    "source": "ACADEMIC",
                    "section": "ACADEMIC",
                    "question_id": q['question_id'],
                    "order": order
                })
                order += 1

        return final_questions
