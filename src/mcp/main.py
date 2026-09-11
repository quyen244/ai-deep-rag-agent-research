from fastmcp import FastMCP

mcp = FastMCP('Demo 🚀')


@mcp.tool
def add(a : int , b : int) -> int:
    """ add two numbers. """
    return a + b 

@mcp.tool
def greet(name : str) -> str:
    return f"Hello , {name} !"

@mcp.prompt
def code_review(language : str , code_snippet : str) -> str:
    """Create a review code template by language."""
    return f"""Hãy review đoạn code {language} sau đây và đề xuất cải thiện.
    
            ```{language}
                {code_snippet}
            ```
    
            """



if __name__ == "__main__" :
    # mcp.run()  # mặc định stdio
    # hoặc
    mcp.run()
    




