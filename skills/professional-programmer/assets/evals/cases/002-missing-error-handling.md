# 002 Missing Error Handling

An API handler catches provider errors and returns success with an empty array to avoid showing errors to users.

The endpoint feeds a dashboard where false success would hide provider outages from operators.
