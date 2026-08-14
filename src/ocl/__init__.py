import argparse


def main() -> None:
    argument = "Hello from ocl!"
    argparser = argparse.ArgumentParser(description="OptimizedClaude")
    argparser.add_argument(
        "--version",
        action="version",
        version="ocl 0.1.0",
    )
    print(argument)
