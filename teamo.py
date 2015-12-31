#!/usr/bin/env python


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
