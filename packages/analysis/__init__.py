"""Deterministic analysis for the report page.

Every function here takes sourced inputs and returns either a value together
with the inputs it used, or an Unavailable object that says why. No function
returns a default number when an input is missing.
"""
