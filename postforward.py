#!/usr/bin/env python3

import argparse
import sys
import email
import socket
from subprocess import Popen, PIPE
from email.parser import Parser
from email.policy import default

parser = argparse.ArgumentParser(description="Postfix SRS forwarding agent.")
parser.add_argument("to")
parser.add_argument(
    "--dry-run",
    required=False,
    dest="dryrun",
    action="store_true",
    help="Show what would be done, don't actually forward mail",
)
parser.add_argument(
    "--rp-header",
    type=str,
    default="Return-Path",
    dest="rpheader",
    required=False,
    help="Header name containing the mail from value. Default: Return-Path",
)
parser.add_argument(
    "--srs-addr",
    type=str,
    dest="srsaddr",
    required=False,
    default="localhost:10001",
    help="TCP address for SRS lookups. Default: localhost:10001",
)


def _getSRSReturnPath(address, SRSHOST, SRSPORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((SRSHOST, SRSPORT))
        try:
            command = "get %s\n" % address
            sock.sendall(command.encode())
            result = sock.recv(512).decode()
            resultCode = int(result[:3])
            if resultCode == 200:
                resultSRSReturnPath = str(result[4:]).strip()
                return resultSRSReturnPath
            else:
                pass
        finally:
            sock.close()


def _getHostname():
    return socket.gethostname()


def _getRFC5322DateTime():
    return email.utils.format_datetime(email.utils.localtime())


def main():
    args = parser.parse_args()
    TO = str(args.to)
    DRYRUN = bool(args.dryrun)
    RETURNPATHHEADER = str(args.rpheader)
    SRSHOST = str(args.srsaddr.split(":")[0])
    SRSPORT = int(args.srsaddr.split(":")[1])

    message = Parser(policy=default).parsestr(sys.stdin.read())
    returnPath = message[RETURNPATHHEADER].lstrip("<").rstrip(">")
    SRSReturnPath = _getSRSReturnPath(returnPath, SRSHOST, SRSPORT)

    message.add_header(
        "Received", "by %s (Postforward); %s" % (_getHostname(), _getRFC5322DateTime())
    )
    message.add_header("X-Original-Return-Path", SRSReturnPath)
    message.replace_header("Return-Path", SRSReturnPath)

    sendmailArgs = ["sendmail", "-i", "-f", SRSReturnPath, TO]
    if DRYRUN == True:
        print("Would call sendmail with args: %s" % " ".join(sendmailArgs))
        print("Would pipe the folliwng data into sendmail:\n")
        print(message.as_string())
    else:
        sendmail = Popen(sendmailArgs, stdin=PIPE, universal_newlines=True)
        sendmail.communicate(message.as_string())


if __name__ == "__main__":
    main()
