import numpy as np

from teamo import (match_counts, unique_students, unique_projects,
                   equality_constraints, choose_projects,
                   MultipleChoiceSingleAnswerQuestion)


def test_match_counts():

    team_array = np.array([[0, 1, 2, np.nan],
                           [3, 4, 5, 6]])

    choices = {0: ['a', 'b', 'c'],
               1: ['c', 'd', 'e'],
               2: ['b', 'c', 'a'],
               3: ['f', 'g', 'h', 'i'],
               4: ['a', 'f', 'h'],
               5: ['c', 'f', 'e'],
               6: ['c', 'a', 'e']}

    expected_counts = {
                    (0, 1, 2): {'a': 2, 'b': 2, 'c': 3, 'd': 1, 'e': 1},
                    (3, 4, 5, 6): {'a': 2, 'c': 2, 'e': 2, 'f': 3, 'g': 1,
                                   'h': 2, 'i': 1}
                   }

    counts = match_counts(team_array, choices)

    assert counts == expected_counts

    # This should effectively ignore the student 10 which is not in the
    # choices.
    team_array = np.array([[0, 1, 2, 10],
                           [3, 4, 5, 6]])

    counts = match_counts(team_array, choices)

    assert counts == expected_counts


def test_unique_students():

    students = np.array([[0, 1, 2, np.nan],
                         [3, 4, 5, 6]])

    assert unique_students(students) == 0

    students = np.array([[0, 1, 2, np.nan],
                         [3, 4, 2, 6]])

    assert unique_students(students) == 1

    students = np.array([[0, 1, 2, 9999],
                         [3, 4, 5, 6]])

    assert unique_students(students) == 0

    students = np.array([[0, 1, 2, 9999, 9999],
                         [3, 4, 2, 6, 7]])

    assert unique_students(students) == 1

    students = np.array([[0, 1, 2, 9999, 9999],
                         [3, 4, 5, 6, 7]])

    assert unique_students(students) == 0

def test_unique_projects():

    projects = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']

    assert unique_projects(projects) == 0

    projects = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'h']

    assert unique_projects(projects) == 1


def test_equality_constraints():

    students = np.array([0, 1, 2, np.nan, 3, 4, 5, 6])
    projects = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'h']

    np.testing.assert_allclose([0, 1], equality_constraints(students, projects))


def test_match_cost():

    choices = {0: ['a', 'b', 'c'],
               1: ['c', 'd', 'e'],
               2: ['b', 'c', 'a'],
               3: ['f', 'g', 'h', 'i'],
               4: ['a', 'f', 'h'],
               5: ['c', 'f', 'e'],
               6: ['c', 'a', 'e']}

    match_counts = {
                    {0, 1, 2}: {'a': 2, 'b': 2, 'c': 3, 'd': 1, 'e': 1},
                    {3, 4, 5, 6}: {'a': 2, 'c': 2, 'e': 2, 'f': 3, 'g': 1,
                                   'h': 2, 'i': 1}
                   }

    teams = {'c': {0, 1, 2},
             'f': {3, 4, 5, 6}}

    expected_cost = (3 / 3 + 3 / 4) / 2

    cost = match_cost(choices)

    np.testing.assert_allclose(cost, expected_cost)


def test_choose_projects():

    x = [0, 1, 2, np.nan, 3, 4, 5, 6]
    choices = {0: ['a', 'b', 'c'],
               1: ['c', 'd', 'e'],
               2: ['b', 'c', 'a'],
               3: ['f', 'g', 'h', 'i'],
               4: ['a', 'f', 'h'],
               5: ['c', 'f', 'e'],
               6: ['c', 'a', 'e']}
    project_list = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']


    expected_teams = {'c': {0, 1, 2},
                      'f': {3, 4, 5, 6}}

    teams = choose_projects(x, choices, project_list)

    assert teams == expected_teams


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
