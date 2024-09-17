import subprocess
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

def run_modal_command(command, function_name=None):
    if command == "deploy":
        modal_command = ["modal", "deploy", "first_gen.py"]
    elif command == "shell":
        if not function_name:
            raise ValueError("Function name is required for shell command")
        modal_command = ["modal", "shell", f"first_gen.py::{function_name}"]
    elif command == "serve":
        modal_command = ["modal", "serve", "first_gen.py"]
    else:
        raise ValueError("Invalid command. Use 'deploy', 'serve', or 'shell'")

    try:
        process = subprocess.Popen(
            modal_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        for line in process.stdout:
            print(line, end='')
            sys.stdout.flush()

        return_code = process.wait()
        if return_code != 0:
            print(f"Command failed with return code {return_code}")
            return False
        return True
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Modal commands")
    parser.add_argument("command", choices=["deploy", "serve", "shell"], help="Command to run (deploy, serve, or shell)")
    parser.add_argument("--function", help="Function name for shell command")
    args = parser.parse_args()

    if args.command == "shell" and not args.function:
        parser.error("The shell command requires a function name (use --function)")

    success = run_modal_command(args.command, args.function)
    print("Command executed successfully" if success else "Command failed")
