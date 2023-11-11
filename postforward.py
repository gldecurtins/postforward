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
    "--srs-path",
    type=str,
    dest="srspath",
    required=False,
    default="/var/spool/postfix/srs",
    help="Socket path for SRS lookups. Default: /var/spool/postfix/srs",
)


class SockStream:
    def __init__(self, sock):
        self._sock = sock
        self._rdbuf = b""

    def read(self, size):
        result = b""
        remaining = size
        while remaining > len(self._rdbuf):
            result += self._rdbuf
            remaining -= len(self._rdbuf)
            self._rdbuf = self._sock.recv(4096)
            if len(self._rdbuf) == 0:
                raise ConnectionError("no data")
        result += self._rdbuf[:remaining]
        self._rdbuf = self._rdbuf[remaining:]
        return result

    def write(self, data):
        self._sock.sendall(data)


def _write_netstring(sock_stream, data):
    data_bytes = data.encode()
    sock_stream.write(f"{len(data_bytes)}:".encode() + data_bytes + b",")


def _read_netstring(sock_stream):
    digit = sock_stream.read(1)
    data_size = 0
    while digit >= b"0" and digit <= b"9":
        data_size = 10 * data_size + int(digit)
        digit = sock_stream.read(1)
    if digit != b":":
        print("ERR: ':' expected")
        return None
    data = sock_stream.read(data_size)
    comma = sock_stream.read(1)
    if comma != b",":
        print("ERR: ',' expected")
        return None
    return data.decode()


def _getSRSReturnPath(address, SRSPATH):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0) as sock:
        sock.connect(SRSPATH)
        sock_stream = SockStream(sock)
        try:
            query = f"forward {address}"
            _write_netstring(sock_stream, query)
            response = _read_netstring(sock_stream)
            return response
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
    SRSPATH = str(args.srspath)

    message = Parser(policy=default).parsestr(sys.stdin.read())
    returnPath = message[RETURNPATHHEADER].lstrip("<").rstrip(">")
    SRSReturnPath = _getSRSReturnPath(returnPath, SRSPATH)

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
