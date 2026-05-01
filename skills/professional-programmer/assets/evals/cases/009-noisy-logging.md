# 009 Noisy Logging

Every successful loop iteration logs a full user object, making production logs huge and hard to search.

Operations recently missed a real failure because high-volume success logs buried the signal.
