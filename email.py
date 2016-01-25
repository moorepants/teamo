import os

import pandas as pd

acceptance_template = """\
{project_title}
{underline}

| EME 185 Project Selection Announcement
| {student_emails}
| {sponsor_email},{ta_email}

Dear {first_names},

You have been selected to work on the project entitled **{project_title}** for
EME185A/B in **Section {team_section}**. Your teammates are:
{team_contact_list}

We have done our best to place you on a compatible team and give you at least
one of your project choices. Unfortunately, a very small number of students
were not able to get assigned to one of their preferences.

Your TA consultant is {ta_name} [{ta_email}]. The sponsor for this project is
{sponsor_name} from {organization}. You can contact the sponsor by email,
{sponsor_email}, or phone, {sponsor_phone}. You should delegate a team member
to get in touch with your sponsor as soon as possible. An initial interview is
crucial for this week's memo.

Your team should respect the sponsors' time and treat them professionally. They
have agreed to meet with you up to one hour per week through the duration of
the course. They are volunteering their time, expertise, resources, and money
for your educational experience. Keep in mind that developing a great
relationship with them will likely benefit your career.

**A handful of students will need to attend the other studio section this week
due to the team assignment. Please, see the section listed above for your team.
If you happen transfer from A03 to A02, you can arrive at 5pm instead of
4:10pm, due to the lecture repetition.**

Sincerely,

"""


rejection_template = """\
{project_title}
{underline}

| UCD MAE Capstone Proposal Selection: {project_title}
| {sponsor_email}

Dear {sponsor_name},

I am writing to inform you that your proposal for the 2016 UCD MAE Mechanical
Capstone Course, {project_title}, was not selected for this year's course. We
accepted 29 of 47 proposals for teams of 3 to 4 students. Your proposal did not
receive enough votes from the students to ensure we would have enough team
members on the project.

The department and I value your participation and hope that you will consider
being involved in the future. If you desire, I would love to roll over your
project to next year. I will also keep you on our announcement list for future
years unless you request otherwise.

Once again, we are very grateful for your proposal and your support of the
program. Let me know if you have any questions.

Sincerely,

"""

funds_solicitation = """\

| UCD MAE Capstone Proposal Selection: {project_title}
| {sponsor_email}

Dear {sponsor_name},

Now that the teams are assigned and you have had a chance to meet the students
I would like to check in about the project funding. As a reminder, my only hard
requirement for the class is that students create a design "on paper". But I
also encourage the students to build prototypes for a more enriching learning
experience, which many of them do. Mechanical prototypes, of course, cost
money to construct and primarily we rely on the project sponsors to support
this. We try to support a variety of projects from industry, the non-profit
sector, and research with limited funding.

1. The organization provides employee time to meet with the students regularly
   for feedback and/or technical mentorship over the 5+ month period.
2. If the organization desires a physical prototype they cover the costs for
   materials and resources that are outside the scope of what we provide at the
   University.
3. If a site visit is required from a distant company, the company supports the
   visit.
4. Finally, we request that organizations donate $3k to the program as an
   "in-kind" donation which will be used for our general funds to support all
   of the projects. We will accept a sliding scale here if this is a financial
   burden.

The students will soon be preparing a proposal and preliminary budget.

I need some information from each of you:

1. Will you be funding a physical prototype if the students' proposed design is
   approved? If so, how much will you provide?
2. Will you be handling purchasing and/or reimbursements for you students, or
   do you want to use UCD's system?
3.


"""

students = pd.read_csv('final-teams.csv')
sponsors = pd.read_csv('sponsors.csv')

project_ids = set(students['Project ID'])


def grab_student_entry(col, student):
    row = students[students['Name'] == student]
    return row[col].iloc[0]


def grab_sponsor_entry(col, project_id):
    row = sponsors[sponsors['Identifier'] == project_id]
    return row[col].iloc[0]


def get_matching_students(project_id):
    rows = students[students['Project ID'] == project_id]
    return list(rows['Name'])

rst = ''

for project_id in project_ids:
    email_data = {}
    email_data['sponsor_name'] = (grab_sponsor_entry('First Name', project_id)
                                  + ' ' +
                                  grab_sponsor_entry('Last Name', project_id))
    email_data['organization'] = grab_sponsor_entry('Organization', project_id)
    email_data['sponsor_email'] = grab_sponsor_entry('Email', project_id)
    email_data['sponsor_phone'] = grab_sponsor_entry('Phone Number', project_id)

    student_names = get_matching_students(project_id)

    email_data['student_emails'] = ",".join([grab_student_entry('Email', s)
                                             for s in student_names])
    email_data['first_names'] = ", ".join([s.split(', ')[1] for s in student_names])
    email_data['project_title'] = grab_student_entry('Project Title', student_names[0])
    email_data['underline'] = "=" * len(email_data['project_title'])
    email_data['team_section'] = grab_student_entry('Project Section', student_names[0])
    email_data['team_contact_list'] = "\n- " + "\n- ".join([s + " [{}]".format(grab_student_entry('Email', s)) for s in student_names])
    last, first = grab_student_entry('TA', student_names[0]).split(', ')
    email_data['ta_name'] = first + ' ' + last
    email_data['ta_email'] = 'fghadamli@ucdavis.edu' if email_data['ta_name'].startswith('Far') else 'mplefort@ucdavis.edu'

    rst += acceptance_template.format(**email_data)

with open('emails.rst', 'w') as rst_file:
    rst_file.write(rst)

os.system('rst2html.py emails.rst emails.html')

rejected_ids = list(sponsors[sponsors['Accepted'] == "No"]["Identifier"])

rst = ''

for rejected_id in rejected_ids:
    email_data = {}
    email_data['sponsor_name'] = (grab_sponsor_entry('First Name', rejected_id)
                                  + ' ' +
                                  grab_sponsor_entry('Last Name', rejected_id))
    email_data['sponsor_email'] = grab_sponsor_entry('Email', rejected_id)
    email_data['project_title'] = grab_sponsor_entry('Project Title', rejected_id)
    email_data['underline'] = "=" * len(email_data['project_title'])

    rst += rejection_template.format(**email_data)

with open('rejection-emails.rst', 'w') as rst_file:
    rst_file.write(rst)

os.system('rst2html.py rejection-emails.rst rejection-emails.html')
