from teamo import (MultipleChoiceSingleAnswerQuestion,
                   UnderrepresentedMemberQuestion, ProjectRankQuestion,
                   compute_num_teams)


def test_num_teams():

    num_people = 70
    min_num_people_per_team = 4

    num_teams, max_in_team, num_large_teams = \
        compute_num_teams(num_people, min_num_people_per_team)

    assert num_teams == 17
    assert max_in_team == 5
    assert num_large_teams == 2

    num_people = 72
    min_num_people_per_team = 4

    num_teams, max_in_team, num_large_teams = \
        compute_num_teams(num_people, min_num_people_per_team)

    assert num_teams == 18
    assert max_in_team == 4
    assert num_large_teams == 0


def test_project_rank_question():

    all_projects = ['A', 'B', 'C', 'D', 'E']
    q = ProjectRankQuestion(all_projects)

    project_assignment = 'A'

    project_choices = [['A', 'B'],
                       ['B', 'A'],
                       ['C', 'A', 'D']]
    score = q.compute_score(project_assignment, project_choices)
    assert score == 1
    score = q.compute_score(project_assignment, project_choices, ordered=True)
    assert score == (3 + 2 + 2) / 9

    project_choices = [['A', 'B'],
                       ['B', 'A'],
                       ['C', 'D']]
    score = q.compute_score(project_assignment, project_choices)
    assert score == 2 / 3
    score = q.compute_score(project_assignment, project_choices, ordered=True)
    assert score == (2 + 1 + 0) / 6


def test_underrepresented_member_question():

    underrep = ['Female', 'Other']
    q = UnderrepresentedMemberQuestion(underrep)

    responses = ['Male', 'Male', 'Male']
    assert q.compute_score(responses) == 0

    responses = ['Male', 'Male', 'Female']
    assert q.compute_score(responses) == -1

    responses = ['Male', 'Female', 'Female']
    assert q.compute_score(responses) == 1


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
