#!/usr/bin/env python

from collections import defaultdict

import numpy as np

"""

Given a list of project preferences for each student we need to form teams
such that:

1. Each team is guaranteed to have at least one common project.
2. Each team is assigned a unique project.
3. Each team should have a unique set of students.
4. The assigned project should be weighted to the top choice(s) of the team
    members.

cost function: 0-1

For no matches in a team: 0
Other: # matches / # team mates
At least one in each team: 1

Cost: # matches / # team mates

# top choices / # team mates

Constraint:

    team 1 proj != team 2 proj != team 3 proj != team N proj

"""


def match_cost(team_array, team_choices):
    """

    N : number of teams
    n : maximum number of teammates (can include nan)

    team_array : ndarray of integers, shape(N, n)
    team_choices : dictionary

    """


    number_of_teams = team_array.shape[0]

    counts = match_counts(team_array, team_choices)

    cost = 0
    for team, matches in counts.items():
        cost += max(matches.values()) / len(team)

    return cost / number_of_teams


def convert_to_int(team_array):

    nan_idx = np.isnan(team_array)
    team_array = team_array.astype(np.int64)
    team_array[nan_idx] = 9999

    return team_array


def choose_projects(team_array, team_choices, project_list):
    """Returns a unique project assignment for each team."""

    project_assignments = {}

    counts = match_counts(team_array, team_choices)

    for team, matches in counts.items():
        for project, val in matches.items():
            if val == max(matches.values()):
                while True:
                    try:
                        project_list.remove(project)
                    except ValueError:
                        continue
                    proj_sel = project
                break
        project_assignments[proj_sel] = team

    return project_assignments


def match_counts(team_array, team_choices):
    """Returns a count of the project matches for each team."""

    team_array = convert_to_int(team_array)

    # TODO : This can probably use colletions.Counter in some to make it
    # faster.

    # If there is a student listed in the team_array that doesn't exist in the
    # team_choices then convert to nan.
    students = team_choices.keys()
    for i, team in enumerate(team_array):
        for j, student in enumerate(team):
            if student not in students:
                team_array[i, j] = 9999

    counts = {}
    for team in team_array:
        team_without_nans = tuple(team[team != 9999])
        counts[team_without_nans] = defaultdict(lambda: 0)
        for student in team_without_nans:
            for choice in team_choices[student]:
                counts[team_without_nans][choice] += 1

    return counts


def unique_students(team_array):
    """Returns 0 if list of students is unique and 1 if not. Ignores nans."""

    students = convert_to_int(team_array).flatten()

    # TODO : remove any students that are equal to 9999

    if len(students) > len(set(students)):
        return 1
    else:
        return 0


def unique_projects(team_array, projects):
    """Returns 0 if the list of projects is unique and 1 if not."""

    if len(projects) > len(set(projects)):
        return 1
    else:
        return 0


def equality_constraints(team_array, project_list):

    return np.array([unique_students(team_array),
                     unique_projects(team_array, project_list)])


class MultipleChoiceSingleAnswerQuestion(object):

    def __init__(self, question, choices):
        self.question = question
        self.choices = choices

    def compute_score(self, responses):
        """Returns the score, where values closer to 0.0 represent homogenity
        in the choice for a given group of responses and values closer to 1.0
        represent heterogenity."""

        score = 0

        for choice in self.choices:
            for response in responses:
                if response == choice:
                    or_result = 1
                    break
                else:
                    or_result = 0
            score += or_result
            or_result = 0

        score = score / len(responses)

        return score
