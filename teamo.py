#!/usr/bin/env python

# builtin
import os
from random import choice
from collections import Counter, defaultdict

# external
import pandas as pd

# local
from parse_rst import parse_document


def compute_num_teams(num_people, min_in_team, max_num_teams):
    """Returns the team numbers.

    Parameters
    ==========
    num_people : integer
        The total number of people available to be on the team.
    min_in_team : integer
        The minimum number of people in a team.
    max_num_teams : integer
        The maximum number of teams that we have tables for.

    Returns
    =======
    num_teams : integer
        The number of teams.
    max_in_team : integer
        The maximum number of members in a team.

    """

    num_teams = num_people // min_in_team
    if num_teams > max_num_teams:
        num_teams = max_num_teams
        num_larger_teams = num_people - num_teams * min_in_team
    else:
        num_larger_teams = num_people % min_in_team
    if num_larger_teams > 0:
        max_in_team = min_in_team + 1
    else:
        max_in_team = min_in_team

    return num_teams, max_in_team, num_larger_teams


def populate_students(roster, catme_data):
    """Returns a dictionary of intialized Person objects representing each
    student.

    Parameters
    ==========
    roster : pandas.DataFrame
        Columns: Name, ID, email, Section
    catme_data : pandas.DataFrame
        An export of the CATME survey with the standard column names.

    Returns
    =======
    students : dictionary of Person
        All of the students in the class keyed by the person's name.

    """
    students = {}
    for roster_idx, roster_row in roster.iterrows():
        name = roster_row['Name']
        section = roster_row['Section']
        row = catme_data[catme_data['Name'] == name]
        if len(row) == 0:
            person = Person(name)
        else:
            r = row[['Project Choice #1',
                     'Project Choice #2',
                     'Project Choice #3',
                     'Project Choice #4',
                     'Project Choice #5']]
            selections = r.values.squeeze().tolist()
            if all(pd.isnull(selections)):
                selections = []
            else:
                selections = [s.lower().strip() for s in selections]
            self_rep_sec = row['Studio Section'].iloc[0]
            if section != self_rep_sec:
                print('{} reported wrong section.'.format(name))
            person = Person(name,
                            section,
                            True if row['Studio Switch'].iloc[0] == 'Yes' else False,
                            row['Sex'].iloc[0],
                            selections,
                            row['GPA'].iloc[0],
                            row['Race'].iloc[0])
        students[person.name] = person
    return students


def populate_projects(project_dir):
    """Returns a dictionary containing all of the projects in the provided
    directory. This directory should contain the Pelican rst files, one for
    each project."""

    field_names_and_parsers = {
        'title': str,
        'org': str,
        'org_url': str,
        'skills': lambda s: [skill.strip() for skill in str(s).split(',')],
        'location': str,
        'id': str,
        'status': str,
        'template': str,
    }
    projects = {}
    for rst_file in os.listdir(project_dir):
        with open(os.path.join(project_dir, rst_file), 'r') as f:
            data = parse_document(f.read(), field_names_and_parsers)
            project = Project(data.metadata['id'], data.metadata['title'])
            projects[project.id] = project

    return projects


def rank_projects(students, projects):
    """Returns a DataFrame with the number of votes that each project
    received."""

    all_votes = []
    for name, person in students.items():
        if person.selections is not None:
            all_votes += person.selections
    c = Counter(all_votes)
    votes = pd.DataFrame(c.most_common(), columns=['id', 'votes'])
    votes.index = votes['id']
    del votes['id']
    zero_votes = set(projects.keys()).difference(set(votes.index))
    z = pd.DataFrame([0] * len(zero_votes),
                     columns=['votes'],
                     index=list(zero_votes))
    votes = votes.append(z)
    titles = pd.Series([p.title for p in projects.values()],
                       index=projects.keys())
    votes['title'] = titles

    return votes


def rank_projects_weighted(students, projects):
    """Returns a DataFrame with the number of weighted votes that each project
    received. If projects were selected as a first choice it gets 5 points and
    if 5th choice it gets 1 point."""
    scores = defaultdict(lambda: 0)
    for name, person in students.items():
        if person.selections:
            scores[person.selections[0]] += 5
            scores[person.selections[1]] += 4
            scores[person.selections[2]] += 3
            scores[person.selections[3]] += 2
            scores[person.selections[4]] += 1
    votes_df = pd.DataFrame({'votes': list(scores.values())},
                            index=scores.keys())
    titles_df = pd.DataFrame({'title': [p.title for p in projects.values()]},
                             index=projects.keys())
    votes_df['title'] = titles_df
    return votes_df.sort_values('votes', ascending=False)


class ChooseAnyOrAllQuestion(object):
    pass

class ScheduleCompatibilityQuestion(object):
    pass

class ProjectRankQuestion(object):

    def __init__(self, projects):

        self.projects = projects

    def compute_score(self, project, responses, ordered=False):
        """Returns a score from 0 to 1."""
        score = 0
        max_rank = max([len(r) for r in responses])
        if ordered:
            for response in responses:
                if project in response:
                    rank = (list(reversed(response)).index(project) +
                            max_rank - len(response) + 1)
                    score += rank
            return score / len(responses) / max_rank
        else:
            for response in responses:
                if project in response:
                    score += 1
        return score / len(responses)


class UnderrepresentedMemberQuestion(object):

    def __init__(self, underrep_groups):

        self.underrep_groups = underrep_groups

    def compute_score(self, responses):

        num_underrep = 0

        for response in responses:  # iterate through student responses
            if response in self.underrep_groups:
                num_underrep += 1

        if num_underrep == 0:
            return 0
        elif num_underrep == 1:
            return -1
        elif num_underrep >= 2:
            return 1


class MultipleChoiceSingleAnswerQuestion(object):
    """Represents a multiple choice question with a single answer.

    Notes
    =====

    See page 7 of LoughRy2010.

    """

    def __init__(self, question, choices):
        """
        Parameters
        ==========
        question : string
            The question.
        choices : iterable
            The possible answers of the question, i.e. the multiple choices.

        """

        self.question = question
        self.choices = choices

    def compute_score(self, responses):
        """Returns the score, where values closer to 0.0 represent homogenity
        in the choice for a given group of responses and values closer to 1.0
        represent heterogenity.

        Parameters
        ==========
        responses : iterable
            An iterable containing the response of each person on the team.
        returns : float
            The score from 0.0 to 1.0.

        """

        score = 0

        for selection in self.choices:
            for response in responses:
                if response == selection:
                    or_result = 1
                    break
                else:
                    or_result = 0
            score += or_result
            or_result = 0

        score = score / len(responses)

        return score


class Person(object):
    """Represents a single person in the pool of potential team members."""

    def __init__(self, name, original_section=None, willing_to_switch=None,
                 gender=None, selections=None, gpa=None, race=None):
        """
        Parameters
        ==========
        name : string
            The full name of the person.
        original_section : string
            The section, A02 or A03, that the student is officially registered
            in.
        willing_to_switch : boolean
            True if the student is willing to switch to the section other than
            the one they are registered for.
        gender : string
            The gender of the person.
        selections : iterable
            The preference of projects selected by this person.

        """
        self.name = name
        self.original_section = original_section
        self.willing_to_switch = willing_to_switch
        self.gender = gender
        self.selections = selections
        self.gpa = gpa
        self.race = race

    def __str__(self):
        s = "Name: {}\n".format(self.name)
        s += "Gender: {}\n".format(self.gender)
        s += "Race: {}\n".format(self.race)
        s += "GPA: {}\n".format(self.gpa)
        s += "Original Section: {}\n".format(self.original_section)
        s += "Willing to switch: {}\n".format(self.willing_to_switch)
        if self.selections is not None:
            s += "Selections: {}\n".format(", ".join(self.selections))
        return s

    def __repr__(self):
        msg = "Person('{}', '{}', {}, '{}', {}, {}, {})"
        return msg.format(self.name, self.original_section,
                          self.willing_to_switch, self.gender, self.selections,
                          self.gpa, self.race)

    def can_attend(self, section):
        """Returns true if the person can attend the provided section."""
        if self.original_section == section or self.willing_to_switch:
            return True
        else:
            return False

    def chose_project(self, proj_id):
        return proj_id in self.selections

    def male(self):
        return self.gender != 'Male'


class Project(object):

    def __init__(self, id, title, team=None):
        self.id = id
        self.title = title
        self.team = team

    def __str__(self):
        s = "[{}] {}\n".format(self.id, self.title)
        if self.team:
            s += "=" * len(s) + "\n"
            s += "Team size: {}\n".format(self.team.num_members())
            s += "Members: {}\n".format("; ".join([m.name for m in
                                                   self.team.members]))
            s += "Genders: {}\n".format(", ".join(
                [m.gender if m.gender else 'None' for m in self.team.members]))
            s += "Section: {}\n".format(self.team.section())
        return s

    def __repr__(self):
        return "Project('{}', '{}')".format(self.id, self.title)


class Team(object):

    def __init__(self, members=None):
        if members is None:
            self.members = []
        else:
            self.members = members

    def num_members(self):
        return len(self.members)

    def num_females(self):
        return len([m for m in self.members if m.gender in
                    ['Female', 'Other/Prefer not to answer']])

    def has_female(self):
        if self.num_females() >= 1:
            return True
        else:
            return False

    def has_only_one_female(self):
        if self.num_females() == 1:
            return True
        else:
            return False

    def section(self):
        num_a02 = 0
        num_a03 = 0
        found_no = False
        for member in self.members:
            if member.original_section == 'A02':
                num_a02 += 1
            if member.original_section == 'A03':
                num_a03 += 1
            if member.willing_to_switch == 'No':
                section = member.original_section
                found_no = True

        if not found_no:
            if num_a02 > num_a03:
                section = 'A02'
            elif num_a03 > num_a02:
                section = 'A03'
            else:
                section = choice(['A02', 'A03'])

        return section
