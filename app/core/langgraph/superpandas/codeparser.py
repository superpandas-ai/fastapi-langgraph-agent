import re
import ast
from textwrap import dedent
from langchain_core.output_parsers.string import StrOutputParser
from typing import Literal, Dict
from pydantic import Field

class CodeBlobOutputParser(StrOutputParser):
    """A custom LangChain output parser to extract code blocks from LLM output."""

    framework: Literal["python", "sql"] = Field(default="python", description="The programming language/framework to parse")
    patterns: Dict[str, str] = Field(
        default={
            "python": r"```(?:py|python)\n(.*?)\n```",
            "sql": r"```(?:sql)?\n(.*?)\n```"
        },
        description="Regex patterns for different code block formats"
    )

    def __init__(self, framework: Literal["python", "sql"] = "python"):
        """
        Initialize the parser with the specified framework.

        Args:
            framework (Literal["python", "sql"]): The programming language/framework to parse.
                Defaults to "python".
        """
        super().__init__(framework=framework)

    def parse(self, text: str) -> str:
        """
        Extract code blocks from the LLM's output. If a valid code block is passed,
        it returns it directly.

        Args:
            text (`str`): LLM's output text to parse.

        Returns:
            `str`: Extracted code block.

        Raises:
            ValueError: If no valid code block is found in the text.
        """
        # Check for "no data" message first
        if "Required information is not available in the given database." in text:
            return "NO_DATA_FOUND"
            
        pattern = self.patterns[self.framework]
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return "\n\n".join(match.strip() for match in matches)

        # Maybe the LLM outputted a code blob directly
        if self.framework == "python":
            try:
                ast.parse(text)
                return text
            except SyntaxError:
                pass
        elif self.framework == "sql":
            # Basic SQL validation - check for common SQL keywords
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]
            if any(keyword.lower() in text.lower() for keyword in sql_keywords):
                return text

        raise ValueError(
            dedent(
                f"""
                Your code snippet is invalid, because the regex pattern {pattern} was not found in it.
                Here is the generated code:
                {text}
                Make sure to include code with the correct pattern, for instance:
                Code:
                ```{self.framework}
                # Your {self.framework} code here
                ```
                """
            ).strip()
        )
