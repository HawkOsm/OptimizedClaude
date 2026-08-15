from ocl.legder import Ledger, UserInput


def test_user_input_roundtrip(tmp_path):
    # Create a temporary file path
    temp_file = tmp_path / "test_ledger.txt"

    # Initialize Ledger with the temporary file path
    ledger = Ledger(str(temp_file))

    # Create a UserInput instance
    user_input = UserInput("Test input")

    # Emit the user input to the ledger
    ledger.emit(user_input)

    # Read the contents of the ledger
    contents = ledger.read()

    # Assert that the contents match the emitted input
    assert UserInput("Test input").text == contents[0].text