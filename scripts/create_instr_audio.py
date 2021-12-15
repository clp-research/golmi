"""File: create_instr_audio.py
Skript to generate spoken instructions using Amazon Polly

Author:
    Karla Friedrichs

Skript To Bachelor Thesis:
    "Modeling collaborative reference in a Pentomino domain using the GOLMI
    framework"

Usage:
    > python3 create_instr_audio.py [-h] -f FILE -o OUT_DIR
"""
import argparse
from boto3 import Session
from contextlib import closing
import os


def synthesize_instr_audios(instruction_file, out_dir, polly):
    """Func: synthesize_instr_audios

    Create audios for a list of instructions.

    The given file should contain one instruction per line. Duplicates are
    removed. An audio is created for each line, using Amazon Polly's
    'Matthew' voice. The audios are saved in separate files, the content in
    lowercase and with removed special characters as a file name.

    Params:
    instruction_file - file containing one instruction per line
    out_dir - directory to save the resulting audio files to
    polly - polly session client
    """
    # read in instructions, remove newlines and duplicates
    special_chars = [" ", ",", ".", "'", "!", "?"]
    instructions = set()
    file = open(instruction_file, encoding="utf-8", mode="r")
    for instr in file:
        instr = instr.strip()
        if len(instr) > 0:
            instructions.add(instr.strip())
    file.close()

    # synthesize audios
    for instr in instructions:
        # create a filename by applying lowercase and removing special characters
        filename = instr.lower()
        for c in special_chars:
            filename = filename.replace(c, "")
        filename += ".mp3"
        # skip if audio already exists
        if os.path.exists(os.path.join(out_dir, filename)):
            print("done this already:", filename)
            continue
        # post to Polly
        response = polly.synthesize_speech(Text=instr,
                                        OutputFormat="mp3",
                                        VoiceId="Matthew",
                                        TextType="text")
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                with open(os.path.join(out_dir, filename), "wb") as file:
                    file.write(stream.read())


# --- command line arguments ---

parser = argparse.ArgumentParser(
    description="Create audio files for a list of instructions.")
parser.add_argument("-f", "--file", type=str, required=True,
                    help="File containing one instruction per line")
parser.add_argument("-o", "--out_dir", type=str, required=True,
                    help="Directory to save the created audio file to")


def main():
    args = parser.parse_args()

    # Define Polly parameters (set using 'export PROFILE=profilename')
    profile_name = os.getenv("PROFILE")
    if not profile_name:
        print("Specify polly profile using 'export PROFILE=profilename'")
        print("You need to set up an AWS configuration, see: " + "https://boto3.amazonaws.com" + "/v1/documentation/api/latest/guide/quickstart.html")
        exit()
    session = Session(profile_name=profile_name)
    polly = session.client("polly")

    synthesize_instr_audios(args.file, args.out_dir, polly)


if __name__ == "__main__":
    main()
