"""The kernel: the fixed frame of a being.

Nothing in this package is learned, and nothing outside it may change it at
run time. The being transforms its memory, its values and (with an integrated
engine) its parameters; it never transforms its kernel.
"""

from freewill.core.kernel.capabilities import Action
from freewill.core.kernel.guard import Guard, KernelViolation

__all__ = ["Action", "Guard", "KernelViolation"]
