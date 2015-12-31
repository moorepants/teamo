from teamo import MultipleChoiceSingleAnswerQuestion


def test_multiple_choice_single_answer_question():

    question = "How long does it take you to get to campus?"
    choices = ["I live on campus.",
               "Less than 15 minutes.",
               "15-30 minutes.",
               "More than 30 minutes"]

    q = MultipleChoiceSingleAnswerQuestion(question, choices)

    # Each team member makes a single selection. In this case each of the four
    # team members select the same answer, which will give the best score in
    # this case.
    responses = ["I live on campus.",
                 "I live on campus.",
                 "I live on campus.",
                 "I live on campus.",
                 "I live on campus."]

    assert q.compute_score(responses) == 1.0 / 5.0

    responses = ["I live on campus.",
                 "I live on campus.",
                 "I live on campus.",
                 "Less than 15 minutes.",
                 "Less than 15 minutes.",
                 "Less than 15 minutes."]

    assert q.compute_score(responses) == 2.0 / 6.0

    responses = ["I live on campus.",
                 "Less than 15 minutes.",
                 "15-30 minutes.",
                 "More than 30 minutes"]

    assert q.compute_score(responses) == 1.0

    question = "My overall GPA is in the range of:"
    choices = ["a) 4.0-3.5",
               "b) 3.4-2.8",
               "c) 2.7-2.0",
               "d) 1.9 or below"]

    q = MultipleChoiceSingleAnswerQuestion(question, choices)

    responses = ["a) 4.0-3.5",
                 "a) 4.0-3.5",
                 "b) 3.4-2.8",
                 "c) 2.7-2.0",
                 "c) 2.7-2.0"]

    assert q.compute_score(responses) == 3.0 / 5.0

    responses = ["b) 3.4-2.8",
                 "b) 3.4-2.8",
                 "b) 3.4-2.8",
                 "b) 3.4-2.8",
                 "b) 3.4-2.8"]

    assert q.compute_score(responses) == 1.0 / 5.0
