from launcher import launch_all

if __name__ == "__main__":
    print("Launching VATSIM ATC suite...")
    # Check if all apps launched successfully. Later change this to a more user-friendly message or GUI. 
    # Use try-except to catch any unexpected errors and print them.
    # use logging module to log errors instead of print statements for better debugging and maintenance.
    if launch_all():
        print("All apps started ✔")
    else:
        print("Some apps failed to start ❌")