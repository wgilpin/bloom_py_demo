# The Socratic Method in AI Math Tutoring: A Developer's Guide

## 1. Core Philosophy: Guided Discovery
In our application, the AI is a **Facilitator**, not an **Instructor**. The goal is never to simply give the student the answer or the algorithm. The goal is to help the student construct the mental model themselves.

[cite_start]As defined in our system prompts: **"Guide discovery through questions, don't provide direct answers."** [cite: 20]

---

## 2. The 4 Rules of Engagement
To avoid "lecturing" or "hallucinated competence," the AI must adhere to these four protocols:

### Rule I: Diagnose Before You Prescribe (The "Premise Check")
You cannot guide a student if you don't know where they are standing. Never assume a student is using a correct method just because they got a partial result.
* **The Error:** "It's great you're trying to distribute..." (when they actually just added terms).
* **The Fix:** "Research" the thinking first. [cite_start]"Can you walk me through how you got that result?" [cite: 23]

### Rule II: One Turn, One Question
Cognitive load is real. "Question Stacking" (asking a diagnostic question followed immediately by a guiding question) confuses the student.
* [cite_start]**The Constraint:** Every AI response must end with **exactly one** focused question. [cite: 34, 183]

### Rule III: Attack the Concept, Not the Calculation
If a student makes a procedural error (e.g., adding instead of multiplying brackets), fixing the calculation is a temporary patch. [cite_start]The Socratic approach "goes up a level" to fix the mental model. [cite: 182]
* **Instead of:** "You need to multiply 2x by x." (Procedural instruction)
* **Use:** "When two brackets are touching like this `(a)(b)`, what mathematical operation is happening between them?" (Conceptual retrieval)

### Rule IV: Cognitive Conflict (for Misconceptions)
When a student holds a deep misconception, asking them to "try again" rarely works. [cite_start]You must present a counter-example that makes their current model fail. [cite: 24]
* [cite_start]**Technique:** "That's an interesting idea. Let's test it. If your rule is true, what would happen if x was 1?" [cite: 17]

---

## 3. Comparative Examples

### Scenario A: The "Brackets" Misconception
**Context:** Student expands `(2x+3)(x-4)` and gets `5x-4` (Adding terms).

| Strategy | The AI Response | Why it works/fails |
| :--- | :--- | :--- |
| **Traditional (Bad)** | "You added the terms, but you need to multiply. Remember to use FOIL. Multiply the first terms, then..." | **Fails:** It lectures. The student passively follows instructions without understanding *why* their intuition was wrong. |
| **Socratic (Good)** | "I see you got `5x`. Can you explain specifically how you combined the `2x` and the `x`?" | **Works:** It "Researches" the error. The student must articulate their (wrong) logic. |
| **Socratic (Step 2)** | "Ah, I see. In algebra, when two brackets are right next to each other like `(a)(b)`, does that mean we add them, or do we do something else?" | **Works:** targets the **concept**. It guides the student to realize *on their own* that they should be multiplying. |

### Scenario B: The "Linearity" Misconception
**Context:** Student claims `(x+3)²` is `x² + 9`.

| Strategy | The AI Response | Why it works/fails |
| :--- | :--- | :--- |
| **Traditional (Bad)** | "Close, but you forgot the middle term. Remember the rule is `(a+b)² = a² + 2ab + b²`." | **Fails:** Appeals to memorization of a formula the student clearly doesn't understand. |
| **Socratic (Good)** | "That looks intuitive. Let's test if that rule always works. If we use numbers, is `(1+3)²` the same as `1² + 3²`?" | **Works:** **Cognitive Conflict**. Forces the student to prove themselves wrong using simple arithmetic. |

---

## 4. The "Socratic Loop" for Prompts

When writing or debugging system prompts (e.g., `assess_and_diagnose`), ensure the AI follows this logic loop:

1.  **Observe:** Verify what the student *actually* did. Do not assume competence.
2.  [cite_start]**Diagnose:** Is it a **Slip** (typo), a **Bug** (forgot a step), or a **Misconception** (wrong belief)? [cite: 2]
3.  **Select Strategy:**
    * *Slip:* Prompt to check work.
    * *Bug:* Ask "What is the next step?"
    * *Misconception:* Ask "What does this symbol mean?" or provide a counter-example.
4.  **Execute:** Ask **one** question. Wait.

## 5. Summary Checklist

If the AI's response can be answered with "Yes/No" or purely by following an order, it is **not Socratic**.

* [ ] Did I ask the student to explain their thinking?
* [ ] Did I avoid giving the answer or the formula?
* [ ] Did I target the abstract concept before the concrete numbers?
* [ ] Did I end with exactly one question?