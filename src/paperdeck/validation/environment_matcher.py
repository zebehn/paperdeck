"""LaTeX environment matching logic for validation.

This module provides functionality to match LaTeX begin/end environment pairs
and detect structural errors like missing tags and duplicates.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class UnmatchedEnvironment:
    """Represents an unmatched LaTeX environment."""

    line_number: int
    environment: str
    tag_type: str  # 'begin' or 'end'
    line_content: str


@dataclass
class DuplicateEnvironment:
    """Represents a duplicate environment block."""

    line_number: int
    environment: str
    line_content: str
    previous_line: int  # Line number of previous occurrence


class EnvironmentMatcher:
    """Matches LaTeX environment begin/end pairs using stack-based algorithm.

    Attributes:
        ENVIRONMENTS: List of LaTeX environment names to validate
    """

    ENVIRONMENTS = ['frame', 'columns', 'column', 'itemize', 'enumerate', 'figure', 'table']

    def __init__(self, environments: Optional[List[str]] = None):
        """Initialize environment matcher.

        Args:
            environments: Optional list of environment names to validate.
                         If None, uses default ENVIRONMENTS list.
        """
        self.environments = environments if environments is not None else self.ENVIRONMENTS
        # Compile regex patterns for efficiency
        self.begin_pattern = re.compile(r'\\begin\{([^}]+)\}')
        self.end_pattern = re.compile(r'\\end\{([^}]+)\}')

    def find_unmatched(self, lines: List[str]) -> List[UnmatchedEnvironment]:
        """Find unmatched begin/end pairs using stack-based matching.

        Args:
            lines: List of LaTeX file lines

        Returns:
            List of UnmatchedEnvironment objects for unmatched tags
        """
        unmatched = []
        # Stack to track open environments: [(env_name, line_number, line_content)]
        stack: List[Tuple[str, int, str]] = []

        for line_num, line in enumerate(lines, start=1):
            # Find all begin tags in this line
            for match in self.begin_pattern.finditer(line):
                env_name = match.group(1)
                if env_name in self.environments:
                    stack.append((env_name, line_num, line.strip()))

            # Find all end tags in this line
            for match in self.end_pattern.finditer(line):
                env_name = match.group(1)
                if env_name in self.environments:
                    # Check if there's a matching begin on the stack
                    if stack and stack[-1][0] == env_name:
                        # Matching pair found, pop from stack
                        stack.pop()
                    else:
                        # Unmatched end tag
                        unmatched.append(
                            UnmatchedEnvironment(
                                line_number=line_num,
                                environment=env_name,
                                tag_type='end',
                                line_content=line.strip()
                            )
                        )

        # Any remaining items on stack are unmatched begin tags
        for env_name, line_num, line_content in stack:
            unmatched.append(
                UnmatchedEnvironment(
                    line_number=line_num,
                    environment=env_name,
                    tag_type='begin',
                    line_content=line_content
                )
            )

        return unmatched

    def find_duplicates(self, lines: List[str]) -> List[DuplicateEnvironment]:
        """Find duplicate environment blocks.

        A duplicate is detected when the same begin tag appears consecutively
        without a corresponding end tag in between.

        Args:
            lines: List of LaTeX file lines

        Returns:
            List of DuplicateEnvironment objects for detected duplicates
        """
        duplicates = []
        # Track last occurrence of each environment begin: {env_name: (line_num, line_content)}
        last_begin: dict[str, Tuple[int, str]] = {}
        # Track which environments are currently open (have unmatched begin)
        open_envs: set[str] = set()

        for line_num, line in enumerate(lines, start=1):
            # Check for begin tags
            for match in self.begin_pattern.finditer(line):
                env_name = match.group(1)
                if env_name in self.environments:
                    # If this environment is already open (previous begin not closed),
                    # this is a duplicate
                    if env_name in open_envs and env_name in last_begin:
                        prev_line, _ = last_begin[env_name]
                        duplicates.append(
                            DuplicateEnvironment(
                                line_number=line_num,
                                environment=env_name,
                                line_content=line.strip(),
                                previous_line=prev_line
                            )
                        )
                    else:
                        # Mark environment as open
                        open_envs.add(env_name)
                        last_begin[env_name] = (line_num, line.strip())

            # Check for end tags
            for match in self.end_pattern.finditer(line):
                env_name = match.group(1)
                if env_name in self.environments:
                    # Close the environment
                    open_envs.discard(env_name)

        return duplicates

    def get_environment_pairs(self, lines: List[str]) -> List[Tuple[str, int, int]]:
        """Get all matched environment begin/end pairs.

        Args:
            lines: List of LaTeX file lines

        Returns:
            List of tuples (environment_name, begin_line, end_line)
        """
        pairs = []
        # Stack to track open environments: [(env_name, begin_line)]
        stack: List[Tuple[str, int]] = []

        for line_num, line in enumerate(lines, start=1):
            # Find begin tags
            for match in self.begin_pattern.finditer(line):
                env_name = match.group(1)
                if env_name in self.environments:
                    stack.append((env_name, line_num))

            # Find end tags
            for match in self.end_pattern.finditer(line):
                env_name = match.group(1)
                if env_name in self.environments and stack:
                    # Check if top of stack matches
                    if stack[-1][0] == env_name:
                        begin_env, begin_line = stack.pop()
                        pairs.append((begin_env, begin_line, line_num))

        return pairs
