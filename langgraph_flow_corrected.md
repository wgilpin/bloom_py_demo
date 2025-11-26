# LangGraph Tutor Agent Flow - CORRECTED

## Complete State Machine Flow (Fixed)

```
                    ┌─────────────────────────────────────────────────┐
                    │              START SESSION                       │
                    │         (create_session called)                  │
                    └──────────────────┬──────────────────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────────────────┐
                    │          EXPOSITION NODE                          │
                    │  • Explains the concept                          │
                    │  • Provides examples                             │
                    │  • Asks if student has questions                 │
                    └──────────────────┬──────────────────────────────┘
                                       │
                           route_from_exposition()
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                     │
        Student says "question"/"practice"        Student still
        "try"/"test"/"quiz"                      in dialogue
                    │                                     │
                    ▼                                     ▼
        ┌────────────────────┐                  ┌──────────────┐
        │  QUESTIONING NODE  │                  │     END      │
        │  • Generates       │                  │ (wait for    │
        │    GCSE question   │                  │  student)    │
        │  • Sets calculator │                  └──────────────┘
        │    visibility      │
        │  • Increments      │
        │    attempt counter │
        └──────┬─────────────┘
               │
               │ route_from_questioning()
               │ → Always END
               ▼
        ┌──────────────┐
        │     END      │
        │ (wait for    │
        │  answer)     │
        └──────┬───────┘
               │
               │ Student submits answer
               │ (route handler detects questioning state
               │  and transitions to evaluation)
               ▼
        ┌────────────────────┐
        │  EVALUATION NODE   │
        │  • Parses JSON     │
        │  • Checks correct  │
        │  • Updates counter │
        │  • Brief feedback  │
        └──────┬─────────────┘
               │
               │ route_from_evaluation()
               │
    ┌──────────┴───────────┐
    │                      │
 correct?              incorrect?
    │                      │
    ▼                      ▼
┌────────────────┐  ┌────────────────────┐
│  Set state to  │  │   Set state to     │
│  "questioning" │  │   "diagnosis"      │
└────┬───────────┘  └────────┬───────────┘
     │                       │
     │                       │ route_from_evaluation()
     │                       │ → "diagnosis"
     │                       ▼
     │              ┌──────────────────────┐
     │              │   DIAGNOSIS NODE     │
     │              │   • Silent analysis  │
     │              │   • Prepares context │
     │              │   • No messages sent │
     │              └──────────┬───────────┘
     │                         │
     │                         │ route_from_diagnosis()
     │                         │ → Always "socratic"
     │                         ▼
     │              ┌──────────────────────────┐
     │              │    SOCRATIC NODE          │
     │              │    • Asks ONE guiding     │
     │              │      question             │
     │              │    • NO answer given      │
     │              │    • Makes student think  │
     │              │    • Encourages discovery │
     │              └──────────┬────────────────┘
     │                         │
     │                         │ route_from_socratic()
     │                         │ → Always END
     │                         ▼
     │              ┌──────────────────────┐
     │              │        END           │
     │              │  (wait for student   │
     │              │   to try again)      │
     │              └──────────┬───────────┘
     │                         │
     │                         │ Student tries again
     │                         │ (route handler detects socratic state
     │                         │  and transitions to evaluation)
     │                         │
     └─────────────────────────┴──────────────┐
                                              │
                                              ▼
                    ┌───────────────────────────────────┐
                    │   Back to QUESTIONING NODE        │
                    │   (generates new question)        │
                    └───────────────────────────────────┘
```

## Key Improvements Over Original

### ✅ What Was Fixed

1. **Conditional Edges Now Work**
   - Each node has a routing function that determines next state
   - Graph properly chains through multiple nodes in one request cycle
   - No more "stuck" states

2. **Diagnosis → Socratic Chain**
   - Previously: Never executed
   - Now: Automatically chains when answer is incorrect

3. **Route Handler Fixed**
   - Old: Manually called nodes based on current state (didn't continue)
   - New: Executes graph flow in loop until reaching END

4. **Socratic Method Implemented**
   - Old: "remember to multiply 5 by every term" (telling)
   - New: "What does the number outside need to multiply?" (asking)

## State Transitions Table

| Current State | Student Action | Next Node(s) | Description |
|--------------|----------------|--------------|-------------|
| **exposition** | Says "question" | questioning | Student requests practice |
| **exposition** | Continues chat | END | Stay in dialogue mode |
| **questioning** | - | END | Wait for student answer |
| **questioning** | Submits answer | evaluation | Route handler transitions |
| **evaluation** | Answer correct | questioning | Generate new question |
| **evaluation** | Answer incorrect | diagnosis → socratic | Chain through both nodes |
| **diagnosis** | - | socratic | Always chains automatically |
| **socratic** | - | END | Wait for student retry |
| **socratic** | Submits answer | evaluation | Route handler transitions |

## Example Flow: Incorrect Answer

```
Student: "yes, give me a question please"
→ exposition (detects "question" keyword)
→ questioning (generates: "Expand 3(y - 4)")
→ END (wait for answer)

Student: "3y - 4"  ❌ (incorrect)
→ evaluation (checks answer: incorrect)
→ diagnosis (silent analysis)
→ socratic (asks: "What does the 3 need to multiply?")
→ END (wait for retry)

Student: "oh! both terms! 3y - 12" ✓ (correct)
→ evaluation (checks answer: correct)
→ questioning (generates new question)
→ END (wait for next answer)
```

## Routing Functions Summary

```python
# Exposition: Check if student wants question
route_from_exposition(state) → "questioning" | "END"

# Questioning: Always wait for answer
route_from_questioning(state) → "END"

# Evaluation: Route based on correctness
route_from_evaluation(state) → "questioning" | "diagnosis"

# Diagnosis: Always chain to socratic
route_from_diagnosis(state) → "socratic"

# Socratic: Always wait for retry
route_from_socratic(state) → "END"
```

## Critical Success Factors

1. **Route Handler Loop**: Continues executing until reaching END
2. **State Detection**: Detects questioning/socratic states and transitions to evaluation
3. **Conditional Edges**: Graph properly configured with routing functions
4. **Socratic Prompt**: Strong guidelines to ask questions, not give answers

---

**Status**: ✅ Fully implemented and tested
**Test Result**: Student answer "3y - 4" correctly triggers diagnosis → socratic flow
**Socratic Response**: "What does the number outside the bracket need to multiply?" ✅

